#!/usr/bin/env python
#
# Paramiko Expect Demo
#
# Written by Fotis Gimian
# http://github.com/fgimian
#
# This script demonstrates the SSHClientInteraction class in the paramiko
# expect library
#
from __future__ import print_function
import traceback

import paramiko
from paramiko_expect import SSHClientInteraction


def main():
    # Set login credentials and the server prompt
    HOSTNAME = 'localhost'
    USERNAME = 'vagrant'
    PASSWORD = 'vagrant'
    PROMPT = 'vagrant@paramiko-expect-dev:~\$\s+'

    # Use SSH client to login
    try:
        # Create a new SSH client object
        client = paramiko.SSHClient()

        # Set SSH key parameters to auto accept unknown hosts
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Connect to the host
        client.connect(hostname=HOSTNAME, username=USERNAME, password=PASSWORD)

        # Create a client interaction class which will interact with the host
        with SSHClientInteraction(client, timeout=10, display=True) as interact:
            interact.expect(PROMPT)

            # Run the first command and capture the cleaned output, if you want
            # the output without cleaning, simply grab current_output instead.
            interact.send('uname -a')
            interact.expect(PROMPT)
            cmd_output_uname = interact.current_output_clean

            # Now let's do the same for the ls command but also set a timeout for
            # this specific expect (overriding the default timeout)
            interact.send('ls -l /')
            interact.expect(PROMPT, timeout=5)
            cmd_output_ls = interact.current_output_clean

            # To expect multiple expressions, just use a list.  You can also
            # selectively take action based on what was matched.

            # Method 1: You may use the last_match property to find out what was
            # matched
            interact.send('/vagrant/examples/paramiko_expect-demo-helper.py')
            interact.expect([PROMPT, 'Please enter your name: '])
            if interact.last_match == 'Please enter your name: ':
                interact.send('Fotis Gimian')
                interact.expect(PROMPT)

            # Method 2: You may use the matched index to determine the last match
            # (like pexpect)
            interact.send('/vagrant/examples/paramiko_expect-demo-helper.py')
            found_index = interact.expect([PROMPT, 'Please enter your name: '])
            if found_index == 1:
                interact.send('Fotis Gimian')
                interact.expect(PROMPT)

            # Send the exit command and expect EOF (a closed session)
            interact.send('exit')
            interact.expect()

        # Print the output of each command
        print('-' * 79)
        print('Cleaned Command Output')
        print('-' * 79)
        print('uname -a output:')
        print(cmd_output_uname)
        print('ls -l / output:')
        print(cmd_output_ls)

    except Exception:
        traceback.print_exc()
    finally:
        try:
            client.close()
        except Exception:
            pass


if __name__ == '__main__':
    main()
