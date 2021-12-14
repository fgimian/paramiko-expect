# -*- coding: utf-8 -*-

import socket

import pytest
try:
    from unittest import mock
except ImportError:
    import mock

import paramiko
import paramiko_expect
from paramiko_expect import SSHClientInteraction

try:
    from contextlib import ExitStack
except ImportError:
    from contextlib2 import ExitStack

prompt = ".*:~#.*"


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

    interact.send('apk add python3')
    interact.expect(prompt, timeout=120)

    interact.send('apk add curl')
    interact.expect(prompt, timeout=120)


def test_02_test_other_commnads(interact):
    interact.send('ls -l /')
    interact.expect(prompt, timeout=5)


def test_03_test_demo_helper(interact):
    interact.expect(prompt)
    interact.send('python3 /examples/paramiko_expect-demo-helper.py')
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


def test_04_tail_line_prefix(interact):
    interact.send('sleep 1; curl -v https://httpbin.org/stream/100')

    def stop_callback(msg):
        return "Connection #0 to host httpbin.org left intact" in msg
    interact.tail(line_prefix="test:",  stop_callback=stop_callback)


def test_04_tail_callback(interact):
    interact.send('sleep 1; curl -v https://httpbin.org/stream/100')

    def stop_callback(msg):
        return "Connection #0 to host httpbin.org left intact" in msg
    interact.tail(line_prefix="test:", callback=lambda p, m: "", stop_callback=stop_callback)


def test_04_tail_empty_response(interact):
    interact.send('sleep 1; curl -v https://httpbin.org/stream/100')

    def stop_callback(msg):
        return "Connection #0 to host httpbin.org left intact" in msg

    with mock.patch.object(interact, 'channel') as channel_mock:
        channel_mock.recv.side_effect = [b""]
        interact.tail(line_prefix="test:", callback=lambda p, m: "", stop_callback=stop_callback)


def test_05_context():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname="localhost", username="root", port=2222, key_filename='./test/id_rsa')
    with SSHClientInteraction(client, timeout=10, display=True) as interact:
        interact.send('ls -all /')
        interact.expect(prompt, timeout=120)


def test_06_take_control_01(interact):
    with ExitStack() as stack:
        mocks = [
            mock.patch('termios.tcsetattr'), mock.patch('termios.tcgetattr'),
            mock.patch('tty.setraw'), mock.patch('tty.setcbreak')
        ]
        [stack.enter_context(m) for m in mocks]

        select_mock = stack.enter_context(mock.patch('select.select'))
        channel_mock = stack.enter_context(mock.patch.object(interact, 'channel'))
        stdin_mock = stack.enter_context(mock.patch('sys.stdin'))

        channel_mock.recv.side_effect = [b"test", b"test"]
        stdin_mock.read.side_effect = [b"ls -all\n", b""]
        select_mock.side_effect = [
            [[stdin_mock], [], []],
            [[stdin_mock, channel_mock], [], []]
        ]
        interact.take_control()


def test_06_take_control_02(interact):
    with ExitStack() as stack:
        mocks = [
            mock.patch('termios.tcsetattr'), mock.patch('termios.tcgetattr'),
            mock.patch('tty.setraw'), mock.patch('tty.setcbreak')
        ]
        [stack.enter_context(m) for m in mocks]

        select_mock = stack.enter_context(mock.patch('select.select'))
        channel_mock = stack.enter_context(mock.patch.object(interact, 'channel'))
        stdin_mock = stack.enter_context(mock.patch('sys.stdin'))

        channel_mock.recv.side_effect = [socket.timeout()]
        stdin_mock.read.side_effect = [b"ls -all\n", b""]
        select_mock.side_effect = [
            [[stdin_mock], [], []],
            [[stdin_mock, channel_mock], [], []]
        ]
        interact.take_control()


def test_06_take_control_03(interact):
    with ExitStack() as stack:
        mocks = [
            mock.patch('termios.tcsetattr'), mock.patch('termios.tcgetattr'),
            mock.patch('tty.setraw'), mock.patch('tty.setcbreak')
        ]
        [stack.enter_context(m) for m in mocks]

        select_mock = stack.enter_context(mock.patch('select.select'))
        channel_mock = stack.enter_context(mock.patch.object(interact, 'channel'))
        stdin_mock = stack.enter_context(mock.patch('sys.stdin'))

        channel_mock.recv.side_effect = [""]
        stdin_mock.read.side_effect = [b"ls -all\n", b""]
        select_mock.side_effect = [
            [[stdin_mock], [], []],
            [[stdin_mock, channel_mock], [], []]
        ]
        interact.take_control()


def test_06_take_control_no_termios_01(interact):
    paramiko_expect.has_termios = False
    import threading
    paramiko_expect.threading = threading

    with ExitStack() as stack:
        channel_mock = stack.enter_context(mock.patch.object(interact, 'channel'))
        stdin_mock = stack.enter_context(mock.patch('sys.stdin'))

        channel_mock.recv.side_effect = [b"test"]
        stdin_mock.read.side_effect = [b"ls -all\n", b""]
        interact.take_control()


def test_06_take_control_no_termios_02(interact):

    paramiko_expect.has_termios = False
    import threading
    paramiko_expect.threading = threading

    with ExitStack() as stack:
        channel_mock = stack.enter_context(mock.patch.object(interact, 'channel'))
        stdin_mock = stack.enter_context(mock.patch('sys.stdin'))

        channel_mock.recv.side_effect = [b""]
        stdin_mock.read.side_effect = [b"ls -all\n", b""]
        interact.take_control()


def test_06_take_control_no_termios_03(interact):
    paramiko_expect.has_termios = False
    import threading
    paramiko_expect.threading = threading

    with ExitStack() as stack:
        channel_mock = stack.enter_context(mock.patch.object(interact, 'channel'))
        stdin_mock = stack.enter_context(mock.patch('sys.stdin'))

        channel_mock().recv.side_effect = [b"test", b"test"]
        stdin_mock.read.side_effect = [b"ls -all\n", EOFError()]
        interact.take_control()


def test_07_close(interact):
    with mock.patch.object(interact, 'channel') as channel_mock:
        channel_mock.close.side_effect = [socket.timeout]
        interact.close()


def test_08_issue_25_skip_newline():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname="localhost", username="root", port=2222, key_filename='./test/id_rsa')
    with SSHClientInteraction(client, timeout=10, display=True) as interact:
        interact.send('ls -all')
        interact.expect(prompt, timeout=5)

        # Do not actually sleep, send a ctrl-c at the end
        interact.send('sleep 1', newline=chr(3))
        interact.expect(prompt, timeout=5)
        interact.send('sleep 1' + chr(3), newline='')
        interact.expect(prompt, timeout=5)

        interact.send('ls -all')
        interact.expect(prompt, timeout=5)

def test_09_utf8(interact):
    interact.send(u'André')
