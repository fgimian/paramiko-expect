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
import sys
import re
import types
import socket
import termios
import tty
import select
import paramiko

class SSHClientInteraction:
    """This class allows an expect-like interface to Paramiko which allows coders
    to interact with applications and the shell of the connected device."""

    def __init__(self, client, timeout=60, newline='\r', buffer_size=1024, display=False):
        """The constructor for our SSHClientInteraction class.

        Arguments:
        client -- A Paramiko SSHClient object

        Keyword arguments:
        timeout -- THe connection timeout in seconds
        newline -- The newline character to send after each command
        buffer_size -- The amount of data (in bytes) that will be read at a time
                       after a command is run
        display -- Whether or not the output should be displayed in real-time as
                   it is being performed (especially useful when debugging)

        """
        self.channel = client.invoke_shell()
        self.newline = newline
        self.buffer_size = buffer_size
        self.display = display
        self.timeout = timeout
        self.current_output = ''
        self.current_output_clean = ''
        self.current_send_string = ''
        self.last_match = ''

    def __del__(self):
        """The destructor for our SSHClientInteraction class."""
        self.close()

    def close(self):
        """Attempts to close the channel for clean completion"""
        try:
            self.channel.close()
        except:
            pass

    def expect(self, re_strings=''):
        """This function takes in a regular expression (or regular expressions)
        that represent the last line of output from the server.  The function
        waits for one or more of the terms to be matched.  The regexes are matched
        using expression \n<regex>$ so you'll need to provide an easygoing regex
        such as '.*server.*' if you wish to have a fuzzy match.

        Keyword arguments:
        re_strings -- Either a regex string or list of regex strings that
                      we should expect.  If this is not specified, then
                      EOF is expected (i.e. the shell is completely closed
                      after the exit command is issued)

        Returns:
        - EOF: Returns -1
        - Regex String: When matched, returns 0
        - List of Regex Strings: Returns the index of the matched string as
                                 an integer

        """

        # Set the channel timeout
        self.channel.settimeout(self.timeout)

        # Create an empty output buffer
        self.current_output = ''

        # This function needs all regular expressions to be in the form of a list, so
        # if the user provided a string, let's convert it to a 1 item list.
        if len(re_strings) != 0 and type(re_strings) == types.StringType:
            re_strings = [re_strings]

        # Loop until one of the expressions is matched or loop forever if nothing is expected (usually used for exit)
        while len(re_strings) == 0 or \
              not [re_string for re_string in re_strings if re.match('.*\n' + re_string + '$', self.current_output, re.DOTALL)]:

            # Read some of the output
            buffer = self.channel.recv(self.buffer_size)

            # If we have an empty buffer, then the SSH session has been closed
            if len(buffer) == 0:
                break

            # Strip all ugly \r (Ctrl-M making) characters from the current read
            buffer = buffer.replace('\r', '')

            # Display the current buffer in realtime if requested to do so (good for
            # debugging purposes)
            if self.display:
                sys.stdout.write(buffer)
                sys.stdout.flush()

            # Add the currently read buffer to the output
            self.current_output += buffer

        # Grab the first pattern that was matched
        if len(re_strings) != 0:
            found_pattern = [(re_index, re_string) for re_index, re_string in enumerate(re_strings) if re.match('.*\n' + re_string + '$', self.current_output, re.DOTALL)]

        self.current_output_clean = self.current_output

        # Clean the output up by removing the sent command
        if len(self.current_send_string) != 0:
            self.current_output_clean = self.current_output_clean.replace(self.current_send_string + '\n', '')

        # Reset the current send string to ensure that multiple expect calls don't result in bad output cleaning
        self.current_send_string = ''

        # Clean the output up by removing the expect output from the end if requested and
        # save the details of the matched pattern
        if len(re_strings) != 0:
            self.current_output_clean = re.sub(found_pattern[0][1] + '$', '', self.current_output_clean)
            self.last_match = found_pattern[0][1]
            return found_pattern[0][0]
        else:
            # We would socket timeout before getting here, but for good measure, let's send back a -1
            return -1

    def send(self, send_string):
        """Saves and sends the send string provided"""
        self.current_send_string = send_string
        self.channel.send(send_string + self.newline)

    def take_control(self):
        """This function is a better documented and touched up version of the posix_shell function
        found in the interactive.py demo script that ships with Paramiko"""

        # Get attributes of the shell you were in before going to the new one
        original_tty = termios.tcgetattr(sys.stdin)
        try:
            tty.setraw(sys.stdin.fileno())
            tty.setcbreak(sys.stdin.fileno())
            
            # We must set the timeout to 0 so that we can bypass times when
            # there is no available text to receive
            self.channel.settimeout(0)
            
            # Loop forever until the user exits (i.e. read buffer is empty)
            while True:
                select_read, select_write, select_exception = select.select([self.channel, sys.stdin], [], [])
                # Read any output from the terminal and print it to the screen.
                # With timeout set to 0, we just can ignore times when there's nothing to receive.
                if self.channel in select_read:
                    try:
                        buffer = self.channel.recv(self.buffer_size)
                        if len(buffer) == 0:
                            break
                        sys.stdout.write(buffer)
                        sys.stdout.flush()
                    except socket.timeout:
                        pass
                # Send any keyboard input to the terminal one byte at a time
                if sys.stdin in select_read:
                    buffer = sys.stdin.read(1)
                    if len(buffer) == 0:
                        break
                    self.channel.send(buffer)
        finally:
            # Restore the attributes of the shell you were in
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, original_tty)
