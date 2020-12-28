
import re
import json
import logging
from time import sleep
from collections import namedtuple

from netaddr import IPNetwork, IPAddress


logger = logging.getLogger("Ciena6500.SwitchConfiguration")


class SwitchConfiguration(object):
    """
    Ciena 6500 Node Setup
    """
    def __init__(self, ip, name, loadout = None, config_file = None, **kwargs):
        logger.info("Configuring node {}, config={}".format(name, config_file))
        self.ip = ip
        # Config name for compatibility - use node_name where possible for
        # clarity since this is a group of devices
        self.name = name
        self.node_name = name
        self.chassis_table = {}
        # default mode to tl1, config can override
        self.mode = kwargs.get("mode", "tl1")

        # Handle loadout config
        self.loadout = loadout or []

        if config_file:
            self.load_config(config_file)

        self.bootstrap()

    def load_config(self, config_file):
        """
        Load the loadout from file
        """
        with open(config_file) as f:
            data = json.loads(f.read())

        self.loadout = []
        for entry in data["loadout"]:
            self.loadout.append(entry)

        # Update mode if needed
        self.mode = data.get("mode") or self.mode

    def bootstrap(self):
        """
        Create all the required eqpt
        """
        logger.info("Bootstrapping {} cards".format(len(self.loadout)))
        bs = CardBootstrapper(self)
        for entry in self.loadout:
            bs.bootstrap(entry)

    def get_chassis(self, chassis):
        return self.chassis_table.get(chassis, None)

    def add_or_get_chassis(self, chassis):
        if chassis not in self.chassis_table:
            self.chassis_table[chassis] = Chassis(chassis, self)

        return self.chassis_table[chassis]


#
# Node elements
#
class Chassis(object):
    def __init__(self, name, config):
        self.name = name
        self.card_table = {}
        self.config = config

    def get_full_name(self):
        return "{node_name}-{name}".format(self.config.node_name, self.name)

    def has_card(self, slot_name):
        return slot_name in self.card_table

    def add_card(self, card):
        card.chassis = self
        self.card_table[card.slot_name] = card
        return card

    def get_card(self, slot_name):
        return self.card_table.get(slot_name)


class Card(object):
    def __init__(self, model, aid, slot_name, fields, statuses):
        self.model = model
        self.slot_name = slot_name
        self.chassis = None
        self.ports = {}
        self.aid = aid
        self.fields = fields
        self.statuses = statuses

    def get_full_name(self):
        return "{chassis_name}-{slot_name}".format(
            self.chassis.get_full_name(), self.slot_name
        )

    def get_full_aid(self):
        return "{}-{}-{}".format(self.aid, self.chassis.name, self.slot_name)

    def add_port(self, klass, name, **kwargs):
        self.ports[name] = klass(name, self.chassis, self, **kwargs)

    @classmethod
    def from_loadout(cls, loadout_card):
        fields = {}
        for f in loadout_card["fields"]:
            eqidx = f.index("=")
            fields[f[:eqidx]] = f[eqidx+1:]

        return Card(
            loadout_card["model"],
            loadout_card["aid"],
            loadout_card["slot"],
            fields,
            loadout_card["statuses"],
        )


#
# Bootstrapping
#

class CardBootstrapper(object):
    """
    Pupolate items in switch config based on the given card type
    """
    def __init__(self, config):
        self.config = config

    def bootstrap(self, loadout_card):
        model = loadout_card["model"]
        func = getattr(self, "_{m}".format(m=model.lower()), None)
        if not func:
            raise ValueError("Unsupported card model: {}".format(model))
        func(loadout_card)

    def _sp2_ntk555fa(self, loadout_card):
        """ SP2_SHELF_PROCESSOR_NTK555FA """
        chassis = self.config.add_or_get_chassis(loadout_card["chassis"])
        if chassis.has_card(loadout_card["slot"]):
            raise ValueError(
                "Bad config, slot {} is already populated in chassis {}".format(
                    loadout_card["slot"], loadout_card["chassis"]
                ))

        card = chassis.add_card(Card.from_loadout(loadout_card))
        card.add_port(MgmtIntf, name="LAN", speed=1000)



#
# Ports
#
class Port(object):
    def __init__(self, name, chassis, card):
        # Default is the <card full name>-<port name>
        self.name = "{}-{}".format(card.get_full_name(), name)


class MgmtIntf(Port):
    def __init__(self, name, chassis, card, speed=1000):
        # This becomes "LAN-<chassis name>-<slot name>"
        self.name = "{}-{}-{}".format(name, chassis.name, card.slot_name)
