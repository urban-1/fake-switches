import logging
import re
import unittest
from functools import wraps
import sys

import pexpect
from hamcrest import assert_that, equal_to

from tests.util.global_reactor import TEST_SWITCHES, SwitchBooter


def with_protocol(test):
    """
    Provides a pexpect client (post-auth) to the test!
    """
    @wraps(test)
    def wrapper(self):
        try:
            logging.info(">>>> CONNECTING [%s]" % self.protocol.name)
            self.protocol.connect()
            logging.info(">>>> START")
            test(self, self.protocol)
            logging.info(">>>> SUCCESS")
        finally:
            self.protocol.disconnect()

    return wrapper


class LoggingFileInterface(object):
    def __init__(self, prefix):
        self.prefix = prefix

    def write(self, data):
        for line in data.rstrip(b'\r\n').split(b'\r\n'):
            logging.info(self.prefix + repr(line))

    def flush(self):
        pass


class ProtocolTester(object):
    def __init__(self,host, port, username, password, config, name=None):
        self.name = name or self.CONF_KEY
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.conf = config

        self.child = None

    def connect(self):
        self.child = pexpect.spawn(self.get_ssh_connect_command())
        self.child.delaybeforesend = 0.0005
        self.child.logfile = None
        self.child.logfile_read = LoggingFileInterface(prefix="[%s] < " % self.name)
        self.child.logfile_send = LoggingFileInterface(prefix="[%s] > " % self.name)
        self.child.timeout = 3

        if self.username:
            logging.info(">>>> LOGIN [{}] with {}".format(self.name, self.username))
            self.login()

    def disconnect(self):
        self.child.close()

    def get_ssh_connect_command(self):
        pass

    def login(self):
        pass

    def rread(self, expected):
        self.read(expected, True)

    def read(self, expected, regex=False):
        self.wait_for(expected, regex)
        logging.debug("   read: matched: {!r}".format(expected))
        logging.debug("   read: before: {!r}".format(self.child.before))
        assert_that(self.child.before, equal_to(b""))

    def readln(self, expected, regex=False):
        self.read(expected + "\r\n", regex=regex)

    def read_lines_until(self, expected):
        self.wait_for(expected)
        lines = self.child.before.decode().split('\r\n')
        return lines

    def read_eof(self):
        self.child.expect(pexpect.EOF)

    def wait_for(self, expected, regex=False):
        pattern = re.escape(expected) if not regex else expected
        self.child.expect(pattern)

    def write(self, data):
        self.child.sendline(data.encode())
        self.read(data + "\r\n")

    def write_invisible(self, data):
        self.child.sendline(data.encode())
        self.read("\r\n")

    def write_stars(self, data):
        self.child.sendline(data.encode())
        self.read(len(data) * "*" + "\r\n")

    def write_raw(self, data):
        self.child.send(data.encode())


class SshTester(ProtocolTester):
    CONF_KEY = "ssh"

    def get_ssh_connect_command(self):
        return (
            'ssh %s@%s -p %s -o StrictHostKeyChecking=no '
            '-o UserKnownHostsFile=/dev/null '
            '-o KexAlgorithms=+diffie-hellman-group1-sha1 '
            '-o LogLevel=ERROR '
        ) % (self.username, self.host, self.port)

    def login(self):
        # self.rread(r'[pP]assword: ')
        self.wait_for('[pP]assword: ', regex=True)
        self.write_invisible(self.password)
        self.wait_for('[>#]$', regex=True)
        # self.rread(r'^.*[>#]$')


class TelnetTester(ProtocolTester):
    CONF_KEY = "telnet"

    def get_ssh_connect_command(self):
        return 'telnet %s %s' \
               % (self.host, self.port)

    def login(self):
        self.wait_for("Username: ")
        self.write(self.username)
        self.wait_for("[pP]assword: ", True)
        self.write_invisible(self.password)
        self.wait_for('[>#]$', regex=True)


class ProtocolTest(unittest.TestCase):
    _tester = SshTester
    test_switch = None

    def setUp(self):
        if not self.test_switch:
            return

        self.booter = SwitchBooter(device_filter={self.test_switch}).boot()

        core_switch = self.booter.get_switch(self.test_switch)

        if not self._tester:
            return
        creds = core_switch._test_creds[self._tester.CONF_KEY]
        username = password = None
        if creds:
            username = password = next(iter(creds))

        self.protocol = self._tester(
            "127.0.0.1",
            core_switch._test_ports[self._tester.CONF_KEY],
            username,
            password,
            config=self.booter.get_config(self.test_switch)
        )

    def tearDown(self):
        self.booter.stop()
