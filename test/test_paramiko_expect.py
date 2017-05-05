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
        
    request.addfinalizer(fin)
    return interact


def test_01_install_python(interact):

    interact.send('apk update')
    interact.expect(prompt, timeout=120)

    interact.send('apk add python')
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
