#!/usr/bin/env python
#
# Paramiko Expect Tail Demo
# 
# Written by Fotis Gimian
# http://github.com/fgimian
#
# This script demonstrates the tail functionality in the SSHClientInteraction class
# in the paramiko expect library
#
import sys
import traceback
import re
import paramiko
from paramikoe import SSHClientInteraction

def main():

    # Set login credentials and the server prompt
    hostname = 'localhost'
    username = 'fots'
    password = 'password'
    prompt = 'fots@fotsies-ubuntu-testlab:~\$ '

    # Use SSH client to login
    try:

        # Create a new SSH client object
        client = paramiko.SSHClient()

        # Set SSH key parameters to auto accept unknown hosts
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Connect to the host
        client.connect(hostname=hostname, username=username, password=password)

        # Create a client interaction class which will interact with the host
        interact = SSHClientInteraction(client, timeout=10, display=False)
        interact.expect(prompt)
        
        # Send the tail command
        interact.send('tail -f /var/log/auth.log')
        
        # Now let the class tail the file for us
        interact.tail(line_prefix=hostname+': ')

    except KeyboardInterrupt:
        print 'Ctrl+C interruption detected, stopping tail'
    except Exception as e:
        traceback.print_exc()
    finally:
        try:
            client.close()
        except:
            pass

if __name__ == '__main__':
    main()
