#
# Paramiko Expect
#
# Written by Fotis Gimian
# http://github.com/fgimian
#
# This library works with a Paramiko SSH channel to provide native SSH
# expect-like handling for servers.  The library may be used to interact
# with commands like 'configure' or Cisco IOS devices or with interactive
# Unix scripts or commands.
#
# You must have Paramiko installed in order to use this library.
#
from __future__ import unicode_literals

import sys
import re
import socket
import struct

# Windows does not have termios
try:
    import termios
    import tty
    has_termios = True
except ImportError:
    import threading
    has_termios = False

import select


class SSHClientInteraction(object):
    """
    This class allows an expect-like interface to Paramiko which allows
    coders to interact with applications and the shell of the connected
    device.

    :param client: A Paramiko SSHClient object
    :param timeout: The connection timeout in seconds
    :param newline: The newline character to send after each command
    :param buffer_size: The amount of data (in bytes) that will be read at
                        a time after a command is run
    :param display: Whether or not the output should be displayed in
                    real-time as it is being performed (especially useful
                    when debugging)
    :param encoding: The character encoding to use.
    """

    def __init__(
        self, client, timeout=60, newline='\r', buffer_size=1024,
        display=False, encoding='utf-8'
    ):
        self.channel = client.invoke_shell()
        self.timeout = timeout
        self.newline = newline
        self.buffer_size = buffer_size
        self.display = display
        self.encoding = encoding

        self.current_output = ''
        self.current_output_clean = ''
        self.current_send_string = ''
        self.last_match = ''

    def __del__(self):
        self.close()

    def close(self):
        """Attempts to close the channel for clean completion."""
        try:
            self.channel.close()
        except:
            pass

    def expect(self, re_strings='', timeout=None):
        """
        This function takes in a regular expression (or regular expressions)
        that represent the last line of output from the server.  The function
        waits for one or more of the terms to be matched.  The regexes are
        matched using expression \n<regex>$ so you'll need to provide an
        easygoing regex such as '.*server.*' if you wish to have a fuzzy
        match.

        :param re_strings: Either a regex string or list of regex strings
                           that we should expect; if this is not specified,
                           then EOF is expected (i.e. the shell is completely
                           closed after the exit command is issued)
        :param timeout: Timeout in seconds.  If this timeout is exceeded,
                        then an exception is raised.
        :return: An EOF returns -1, a regex metch returns 0 and a match in a
                 list of regexes returns the index of the matched string in
                 the list.
        :raises: A socket.timeout exception is raised on timeout.
        """

        # Set the channel timeout
        timeout = timeout if timeout else self.timeout
        self.channel.settimeout(timeout)

        # Create an empty output buffer
        self.current_output = ''

        # This function needs all regular expressions to be in the form of a
        # list, so if the user provided a string, let's convert it to a 1
        # item list.
        if isinstance(re_strings, str) and len(re_strings) != 0:
            re_strings = [re_strings]

        # Loop until one of the expressions is matched or loop forever if
        # nothing is expected (usually used for exit)
        while (
            len(re_strings) == 0 or
            not [re_string
                 for re_string in re_strings
                 if re.match('.*\n' + re_string + '$',
                             self.current_output, re.DOTALL)]
        ):
            # Read some of the output
            current_buffer = self.channel.recv(self.buffer_size)

            # If we have an empty buffer, then the SSH session has been closed
            if len(current_buffer) == 0:
                break

            # Convert the buffer to our chosen encoding
            current_buffer_decoded = current_buffer.decode(self.encoding)

            # Strip all ugly \r (Ctrl-M making) characters from the current
            # read
            current_buffer_decoded = current_buffer_decoded.replace('\r', '')

            # Display the current buffer in realtime if requested to do so
            # (good for debugging purposes)
            if self.display:
                sys.stdout.write(current_buffer_decoded)
                sys.stdout.flush()

            # Add the currently read buffer to the output
            self.current_output += current_buffer_decoded

        # Grab the first pattern that was matched
        if len(re_strings) != 0:
            found_pattern = [(re_index, re_string)
                             for re_index, re_string in enumerate(re_strings)
                             if re.match('.*\n' + re_string + '$',
                                         self.current_output, re.DOTALL)]

        # Clean the output up by removing the sent command
        self.current_output_clean = self.current_output
        if len(self.current_send_string) != 0:
            self.current_output_clean = (
                self.current_output_clean.replace(
                    self.current_send_string + '\n', ''
                )
            )

        # Reset the current send string to ensure that multiple expect calls
        # don't result in bad output cleaning
        self.current_send_string = ''

        # Clean the output up by removing the expect output from the end if
        # requested and save the details of the matched pattern
        if len(re_strings) != 0:
            self.current_output_clean = (
                re.sub(
                    found_pattern[0][1] + '$', '', self.current_output_clean
                )
            )
            self.last_match = found_pattern[0][1]
            return found_pattern[0][0]
        else:
            # We would socket timeout before getting here, but for good
            # measure, let's send back a -1
            return -1

    def send(self, send_string):
        """Saves and sends the send string provided."""
        self.current_send_string = send_string
        self.channel.send(send_string + self.newline)

    def tail(self, line_prefix=None, callback=None):
        """
        This function takes control of an SSH channel and displays line
        by line of output as \n is recieved.  This function is specifically
        made for tail-like commands.

        :param line_prefix: Text to append to the left of each line of output.
                            This is especially useful if you are using my
                            MultiSSH class to run tail commands over multiple
                            servers.
        :param callback: You may optionally supply a callback function which
                         takes two paramaters.  The first is the line prefix
                         and the second is current line of output. The
                         callback should return the string that is to be
                         displayed (including the \n character).  This allows
                         users to grep the output or manipulate it as
                         required.
        """

        # Set the channel timeout to the maximum integer the server allows,
        # setting this to None breaks the KeyboardInterrupt exception and
        # won't allow us to Ctrl+C out of the script
        platform_c_maxint = 2 ** (struct.Struct('i').size * 8 - 1) - 1  
        self.channel.settimeout(platform_c_maxint)

        # Create an empty line buffer and a line counter
        current_line = ''
        line_counter = 0

        # Loop forever, Ctrl+C (KeyboardInterrupt) is used to break the tail
        while True:

            # Read the output one byte at a time so we can detect \n correctly
            buffer = self.channel.recv(1)

            # If we have an empty buffer, then the SSH session has been closed
            if len(buffer) == 0:
                break

            # Strip all ugly \r (Ctrl-M making) characters from the current
            # read
            buffer = buffer.replace('\r', '')

            # Add the currently read buffer to the current line output
            current_line += buffer

            # Display the last read line in realtime when we reach a \n
            # character
            if current_line.endswith('\n'):
                if line_counter and callback:
                    sys.stdout.write(callback(line_prefix, current_line))
                else:
                    if line_counter and line_prefix:
                        sys.stdout.write(line_prefix)
                    if line_counter:
                        sys.stdout.write(current_line)
                sys.stdout.flush()
                line_counter += 1
                current_line = ''

    def take_control(self):
        """
        This function is a better documented and touched up version of the
        posix_shell function found in the interactive.py demo script that
        ships with Paramiko.
        """

        if has_termios:
            # Get attributes of the shell you were in before going to the
            # new one
            original_tty = termios.tcgetattr(sys.stdin)
            try:
                tty.setraw(sys.stdin.fileno())
                tty.setcbreak(sys.stdin.fileno())

                # We must set the timeout to 0 so that we can bypass times when
                # there is no available text to receive
                self.channel.settimeout(0)

                # Loop forever until the user exits (i.e. read buffer is empty)
                while True:
                    select_read, select_write, select_exception = (
                        select.select([self.channel, sys.stdin], [], [])
                    )
                    # Read any output from the terminal and print it to the
                    # screen.  With timeout set to 0, we just can ignore times
                    # when there's nothing to receive.
                    if self.channel in select_read:
                        try:
                            buffer = self.channel.recv(self.buffer_size)
                            if len(buffer) == 0:
                                break
                            sys.stdout.write(buffer)
                            sys.stdout.flush()
                        except socket.timeout:
                            pass
                    # Send any keyboard input to the terminal one byte at a
                    # time
                    if sys.stdin in select_read:
                        buffer = sys.stdin.read(1)
                        if len(buffer) == 0:
                            break
                        self.channel.send(buffer)
            finally:
                # Restore the attributes of the shell you were in
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, original_tty)
        else:
            def writeall(sock):
                while True:
                    buffer = sock.recv(self.buffer_size)
                    if len(buffer) == 0:
                        break
                    sys.stdout.write(buffer)
                    sys.stdout.flush()

            writer = threading.Thread(target=writeall, args=(self.channel,))
            writer.start()

            try:
                while True:
                    buffer = sys.stdin.read(1)
                    if len(buffer) == 0:
                        break
                    self.channel.send(buffer)
            # User has hit Ctrl+Z or F6
            except EOFError:
                pass
