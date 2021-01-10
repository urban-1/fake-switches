# Copyright 2015 Internap.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import os

from twisted.conch import avatar, interfaces as conchinterfaces
from twisted.conch.insults import insults
from twisted.conch.ssh import factory, keys, session
from twisted.cred import portal, checkers
from twisted.cred.credentials import IUsernamePassword, ISSHPrivateKey
from twisted.internet import defer
from zope.interface import implementer

from fake_switches.terminal.ssh import SwitchSSHShell
from fake_switches.transports.base_transport import BaseTransport

# from fake_switches.ciena.c6500.ciena_6500_core import CienaTL1Shell


@implementer(conchinterfaces.ISession)
class SSHDemoAvatar(avatar.ConchUser):
    def __init__(self, username, switch_core, variant="cli"):
        avatar.ConchUser.__init__(self)
        self.username = username
        self.switch_core = switch_core
        self.variant = variant
        self.channelLookup.update({b"session": session.SSHSession})

        netconf_protocol = switch_core.get_netconf_protocol()
        if netconf_protocol:
            self.subsystemLookup.update({b"netconf": netconf_protocol})

    def openShell(self, protocol):
        shell_klass = self.switch_core.get_protocol_shell(self.variant)
        server_protocol = insults.ServerProtocol(
            shell_klass, self, switch_core=self.switch_core
        )
        server_protocol.makeConnection(protocol)
        protocol.makeConnection(session.wrapProtocol(server_protocol))

    def getPty(self, terminal, windowSize, attrs):
        return None

    def execCommand(self, protocol, cmd):
        raise NotImplementedError()

    def closed(self):
        pass

    def windowChanged(self, newWindowSize):
        pass

    def eofReceived(self):
        pass


@implementer(portal.IRealm)
class SSHDemoRealm:
    def __init__(self, switch_core, variant="cli"):
        self.switch_core = switch_core
        self.variant = variant

    def requestAvatar(self, avatarId, mind, *interfaces):
        if conchinterfaces.IConchUser in interfaces:
            return (
                interfaces[0],
                SSHDemoAvatar(
                    avatarId, switch_core=self.switch_core, variant=self.variant
                ),
                lambda: None,
            )
        else:
            raise Exception("No supported interfaces found.")


class SwitchSshService(BaseTransport):
    def __init__(self, ip=None, port=22, switch_core=None, users=None, variant="cli"):
        super(SwitchSshService, self).__init__(ip, port, switch_core, users)
        self.variant = variant

    def hook_to_reactor(self, reactor):
        # FIXME(urban): Any exception in this block is shadowed (by twisted
        # I assume...), ensure your SwitchCore fully implements base
        ssh_factory = factory.SSHFactory()
        ssh_factory.portal = portal.Portal(
            SSHDemoRealm(self.switch_core, variant=self.variant)
        )
        if self.users:
            ssh_factory.portal.registerChecker(
                checkers.InMemoryUsernamePasswordDatabaseDontUse(**self.users)
            )
        else:
            ssh_factory.portal.registerChecker(Free4AllChecker())

        dirname = os.path.dirname(os.path.realpath(__file__))
        priv = dirname + "/keys/fake"
        ssh_factory.publicKeys = {b"ssh-rsa": keys.Key.fromFile(priv + ".pub")}
        ssh_factory.privateKeys = {b"ssh-rsa": keys.Key.fromFile(priv)}

        lport = reactor.listenTCP(
            port=self.port, factory=ssh_factory, interface=self.ip
        )
        logging.info(lport)
        logging.info(
            "%s (SSH): Registered on %s tcp/%s"
            % (self.switch_core.switch_configuration.name, self.ip, self.port)
        )
        return lport


class Free4AllChecker(object):
    """
    Pretend to check pubkey... but actually allow all to enter! This is the
    default mode in some vendors where auth happens later (custom radius auth)
    """

    credentialInterfaces = (ISSHPrivateKey,)

    def requestAvatarId(self, credentials):
        return defer.succeed(None)
