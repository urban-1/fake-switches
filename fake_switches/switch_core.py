# Copyright 2018 Inap.
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
from fake_switches.terminal.ssh import SwitchSSHShell


class SwitchCore(object):
    def __init__(self, switch_configuration):
        self.switch_configuration = switch_configuration

    def launch(self, protocol, terminal_controller):
        raise NotImplementedError()

    @staticmethod
    def get_default_ports():
        raise NotImplementedError()

    def get_netconf_protocol(self):
        raise NotImplementedError()

    def get_http_resource(self):
        raise NotImplementedError()

    def get_protocol_shell(self, variant):
        """
        Allow the config to provide a different shell for the
        given protol. Not all devices' ssh shell behave the same.
        By default return ssh.SwitchSSHShell. Variant is a string
        that is vendor/core specific with the default being "cli".
        An example other variant would be "tl1" (over ssh) for
        optical devices.
        """
        return SwitchSSHShell
