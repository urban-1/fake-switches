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

import warnings

from twisted.internet.protocol import Factory

from fake_switches import transports
from fake_switches.terminal.telnet import SwitchTelnetShell


warnings.warn("Please use transports.telnet_service", DeprecationWarning)


class SwitchTelnetFactory(Factory):
    def __init__(self, switch_core):
        self.switch_core = switch_core

    def protocol(self):
        return SwitchTelnetShell(self.switch_core)


class SwitchTelnetService(transports.SwitchTelnetService):
    def __init__(self, ip, telnet_port=23, switch_core=None, **_):
        warnings.warn("Please use transports.telnet_service", DeprecationWarning)
        super(SwitchTelnetService, self).__init__(
            ip=ip, port=telnet_port, switch_core=switch_core
        )
