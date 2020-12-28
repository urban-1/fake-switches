import logging

from fake_switches import switch_configuration
from fake_switches.arista import arista_core
from fake_switches.brocade import brocade_core
from fake_switches.cisco import cisco_core
from fake_switches.cisco6500 import cisco_core as cisco6500_core
from fake_switches.dell import dell_core
from fake_switches.dell10g import dell_core as dell10g_core
from fake_switches.juniper import juniper_core
from fake_switches.juniper_mx import juniper_mx_core
from fake_switches.juniper_qfx_copper import juniper_qfx_copper_core
from fake_switches.ciena.c6500.ciena_6500_core import BaseCiena6500Core
from fake_switches.ciena.c6500.switch_configuration import (
    SwitchConfiguration as Ciena6500SwitchConfiguration
)


DEFAULT_MAPPING = {
    'arista_generic': (arista_core.AristaSwitchCore, None),
    'brocade_generic': (brocade_core.BrocadeSwitchCore, None),
    'cisco_generic': (cisco_core.CiscoSwitchCore, None),
    'cisco_6500': (cisco6500_core.Cisco6500SwitchCore, None),
    'cisco_2960_24TT_L': (cisco_core.Cisco2960_24TT_L_SwitchCore, None),
    'cisco_2960_48TT_L': (cisco_core.Cisco2960_48TT_L_SwitchCore, None),
    'dell_generic': (dell_core.DellSwitchCore, None),
    'dell10g_generic': (dell10g_core.Dell10GSwitchCore, None),
    'juniper_generic': (juniper_core.JuniperSwitchCore, None),
    'juniper_qfx_copper_generic': (juniper_qfx_copper_core.JuniperQfxCopperSwitchCore, None),
    'juniper_mx_generic': (juniper_mx_core.JuniperMXSwitchCore, None),
    'ciena_6500': (BaseCiena6500Core, Ciena6500SwitchConfiguration),
}


class SwitchFactory(object):
    def __init__(self, mapping=None):
        if mapping is None:
            mapping = DEFAULT_MAPPING
        self.mapping = mapping
        self.logger = logging.getLogger("SwitchFactory")

    def get(self, switch_model, hostname='switch_hostname', password='root', ports=None, **kwargs):
        try:
            core, config = self.mapping[switch_model]
        except KeyError:
            raise InvalidSwitchModel(switch_model)

        # By default use the main config class
        config = config or switch_configuration.SwitchConfiguration

        self.logger.info("Core={}, Config={}".format(
            core.__class__.__name__,
            config.__class__.__name__,
        ))
        print(kwargs)

        return core(
            config(
                '127.0.0.1',
                name=hostname,
                privileged_passwords=[password],
                ports=ports or core.get_default_ports(),
                **kwargs
            )
        )


class SwitchFactoryException(Exception):
    pass


class InvalidSwitchModel(SwitchFactoryException):
    pass
