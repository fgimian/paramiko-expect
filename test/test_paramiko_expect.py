import io
import sys

import pytest
import paramiko
from paramiko_expect import SSHClientInteraction

prompt=".*:~#.*"

@pytest.fixture(scope="module")
def interact(request):

    # Create a new SSH client object
    client = paramiko.SSHClient()
    # Set SSH key parameters to auto accept unknown hosts
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # Connect to the host
    client.connect(hostname="localhost", username="root", port=2222, key_filename='./test/id_rsa')
    # Create a client interaction class which will interact with the host
    interact = SSHClientInteraction(client, timeout=10, display=True)
    
    def fin():
        interact.send('exit')
        interact.expect()
        
        interact.close()

    request.addfinalizer(fin)
    return interact


def test_01_install_python(interact):

    interact.send('apk update')
    interact.expect(prompt, timeout=120)

    interact.send('apk add python')
    interact.expect(prompt, timeout=120)

    interact.send('apk add curl')
    interact.expect(prompt, timeout=120)

def test_02_test_other_commnads(interact):
    interact.send('ls -l /')
    interact.expect(prompt, timeout=5)

def test_03_test_demo_helper(interact):
    interact.expect(prompt)
    interact.send('python /examples/paramiko_expect-demo-helper.py')
    found_index = interact.expect([prompt, '.*Please enter your name:.*'])
    assert interact.last_match == '.*Please enter your name:.*'
    assert found_index == 1

    interact.send('Fotis Gimian')
    interact.expect(prompt)


def test_04_tail(interact):

    interact.send('sleep 1; curl -v https://httpbin.org/stream/100')
    def stop_callback(msg):
       return "Connection #0 to host httpbin.org left intact" in msg
    interact.tail(stop_callback=stop_callback)


def test_05_context():

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname="localhost", username="root", port=2222, key_filename='./test/id_rsa')
    with SSHClientInteraction(client, timeout=10, display=True) as interact:
        interact.send('ls -all /')
        interact.expect(prompt, timeout=120)

def test_06_take_control(interact):
    # TODO: think how to test this one
    pass

