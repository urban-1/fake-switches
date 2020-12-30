# Copyright 2015-2016 Internap.
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
import threading

from fake_switches.switch_factory import SwitchFactory
from fake_switches.transports.http_service import SwitchHttpService
from fake_switches.transports.ssh_service import SwitchSshService
from fake_switches.transports.telnet_service import SwitchTelnetService

from tests.util import _juniper_ports_with_less_ae, unique_port

COMMIT_DELAY = 1

TEST_SWITCHES = {
    "arista": {
        "model": "arista_generic",
        "hostname": "my_arista",
        "ssh": {"port": "allocate"},
        "http": {"port": "allocate"},
        "extra": {},
    },
    "brocade": {
        "model": "brocade_generic",
        "hostname": "my_switch",
        "ssh": {"port": "allocate"},
        "extra": {"password": "Br0cad3"},
    },
    "cisco": {
        "model": "cisco_generic",
        "hostname": "my_switch",
        "telnet": {"port": "allocate"},
        "ssh": {"port": "allocate"},
        "extra": {"password": "CiSc000"},
    },
    "cisco-auto-enabled": {
        "model": "cisco_generic",
        "hostname": "my_switch",
        "telnet": {"port": "allocate"},
        "ssh": {"port": "allocate"},
        "extra": {"auto_enabled": True},
    },
    "cisco6500": {
        "model": "cisco_6500",
        "hostname": "my_switch",
        "telnet": {"port": "allocate"},
        "ssh": {"port": "allocate"},
        "extra": {},
    },
    "ciena6500": {
        "model": "ciena_6500",
        "hostname": "eu-uk-not1-1",
        "ssh": {
            "port": "allocate",
            "user": None,
            "variant": "tl1",
        },
        "extra": {"config_file": "tests/config/c6500.json"},
    },
    "dell": {
        "model": "dell_generic",
        "hostname": "my_switch",
        "telnet": {"port": "allocate"},
        "ssh": {"port": "allocate"},
        "extra": {"password": "DeLL10G"},
    },
    "dell10g": {
        "model": "dell10g_generic",
        "hostname": "my_switch",
        "telnet": {"port": "allocate"},
        "ssh": {"port": "allocate"},
        "extra": {"password": "DeLL"},
    },
    "juniper": {
        "model": "juniper_generic",
        "hostname": "ju_ju_ju_juniper",
        "ssh": {"port": "allocate"},
        "extra": {"ports": _juniper_ports_with_less_ae()},
    },
    "juniper_qfx": {
        "model": "juniper_qfx_copper_generic",
        "hostname": "ju_ju_ju_juniper_qfx_copper",
        "ssh": {"port": "allocate"},
        "extra": {"ports": _juniper_ports_with_less_ae()},
    },
    "juniper_mx": {
        "model": "juniper_mx_generic",
        "hostname": "super_juniper_mx",
        "ssh": {"port": "allocate"},
        "extra": {},
    },
    "commit-delayed-arista": {
        "model": "arista_generic",
        "hostname": "my_arista",
        "ssh": {"port": "allocate"},
        "extra": {"commit_delay": COMMIT_DELAY},
    },
    "commit-delayed-brocade": {
        "model": "brocade_generic",
        "hostname": "my_switch",
        "ssh": {"port": "allocate"},
        "extra": {"commit_delay": COMMIT_DELAY},
    },
    "commit-delayed-cisco": {
        "model": "cisco_generic",
        "hostname": "my_switch",
        "ssh": {"port": "allocate"},
        "extra": {"commit_delay": COMMIT_DELAY},
    },
    "commit-delayed-dell": {
        "model": "dell_generic",
        "hostname": "my_switch",
        "ssh": {"port": "allocate"},
        "extra": {"commit_delay": COMMIT_DELAY},
    },
    "commit-delayed-dell10g": {
        "model": "dell10g_generic",
        "hostname": "my_switch",
        "ssh": {"port": "allocate"},
        "extra": {"commit_delay": COMMIT_DELAY},
    },
    "commit-delayed-juniper": {
        "model": "juniper_generic",
        "hostname": "ju_ju_ju_juniper",
        "ssh": {"port": "allocate"},
        "extra": {"commit_delay": COMMIT_DELAY},
    },
}


from twisted.internet import reactor, defer


class ThreadedReactor(threading.Thread):
    def __init(self):
        super().__init__()

    def run(self):
        logging.info("Starting reactor")
        # Blocking
        reactor.run(installSignalHandlers=False)

    def stop(self):
        logging.info("Stoping reactor")
        reactor.callFromThread(reactor.stop)
        logging.info("Stoped reactor")


class SwitchBooter:
    """
    Run a switch on the global reactor - only ONE switch should be
    running at any time - see ThreadedReactor.stop()
    """

    # Supported test services and they primary class
    SVCS = {
        "telnet": SwitchTelnetService,
        "ssh": SwitchSshService,
        "http": SwitchHttpService,
    }

    def __init__(self, device_filter):
        self.reactor = reactor
        self._switches = {}
        self._configs = {}
        self._device_filter = device_filter or {}
        self._booted_ports = []

    def boot(self):
        switch_factory = SwitchFactory()

        def _get_creds(conf, service="ssh"):
            # Disable auth
            if conf[service].get("user", "default") is None:
                return {}

            return {"root": b"root"}

        def _get_port(conf, service="ssh"):
            port = conf[service].get("port")
            if port != "allocate":
                return port
            return unique_port()

        for name, conf in TEST_SWITCHES.items():
            if self._device_filter and name not in self._device_filter:
                continue

            logging.info("Booting config {}: {}".format(name, conf))

            switch_core = switch_factory.get(
                conf["model"], hostname=conf["hostname"], **conf["extra"] or {}
            )

            # Some test meta
            switch_core._test_ports = {}
            switch_core._test_creds = {}

            for svc, svc_klass in self.SVCS.items():
                if svc not in conf:
                    continue

                # Setup this service
                switch_core._test_ports[svc] = _get_port(conf, svc)
                switch_core._test_creds[svc] = _get_creds(conf, svc)
                other_settings = {}
                if svc == "ssh":
                    other_settings = {"variant": conf["ssh"].get("variant", "cli")}

                logging.info(
                    "Booter [{}]: starting service '{}'' on port {}".format(
                        name, svc, switch_core._test_ports[svc]
                    )
                )
                svc_instance = svc_klass(
                    "127.0.0.1",
                    port=switch_core._test_ports[svc],
                    switch_core=switch_core,
                    users=switch_core._test_creds[svc],
                    **other_settings
                )
                self._booted_ports.append(svc_instance.hook_to_reactor(reactor))

            # Register this core and its config to make it accessible to tests
            self._switches[name] = switch_core
            self._configs[name] = conf

        return self

    def get_switch(self, name):
        return self._switches[name]

    def get_config(self, name):
        return self._configs[name]

    def stop(self):
        """ Defer and wait for all ports to stop """
        logging.info("Stopping {} services".format(len(self._booted_ports)))
        defered = [
            defer.maybeDeferred(port.stopListening)
            for port in self._booted_ports
            if port
        ]

        result = defer.gatherResults(defered)


if __name__ == "__main__":
    print("Starting reactor...")
    ThreadedReactor().start()
    SwitchBooter(sys.argv[1]).boot()
    ThreadedReactor().stop()
