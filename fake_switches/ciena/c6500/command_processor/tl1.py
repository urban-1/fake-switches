import time
from random import randint
from datetime import datetime

from fake_switches.command_processing.base_command_processor import BaseCommandProcessor



class TL1Entry:
    def __init__(self, aid, type_, fields, statuses=None):
        self.aid = aid
        self.type = type_ or ""
        self.fields = fields
        self.statuses = statuses or []

    def _fields_str(self):
        fields_str = []
        for k, v in self.fields.items():
            if "\"" in v:
                v = '{}'.format(v.replace("\"", "\\\""))
            fields_str.append("{}={}".format(k, v))
        return ",".join(fields_str)

    def _statuses_str(self):
        if len(self.statuses) == 1:
            return self.statuses[0] + ","
        return ",".join(self.statuses)

    def __str__(self):
        return "{}:{}:{}:{}".format(
            self.aid, self.type, self._fields_str(), self._statuses_str()
        )


class TL1Response:
    ERRORS = {
        # No ctag
        "IICT": "/*Input, Invalid Correlation Tag*/",
        # Bad command
        "ICNV": "/*Input, Command Not Valid*/",
        # Bad/Missing AID
        "IITA": "/*Input, Invalid TArget identifier*/",
        # Not authed
        "PLNA": "/*Privilege, Login Not Active*/",
        # Missing args (pos 4:6)
        "IPMS": "/*Input, Parameter MiSsing*/",
        # Missing Ctag column completely
        "IBMS": "/*Input, Block MiSsing*/",
    }

    ENTRIES_PRE_PAGE = 10
    TAB = "   "

    @classmethod
    def header(cls, node_name, ctag="0", type_="M", verb="COMPLD"):
        return (
            "\r\n{}\"{}\" {}\r\n"
            "{}  {} {}"
        ).format(
            cls.TAB, node_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            type_, ctag, verb,
        )

    @classmethod
    def error(cls, node_name, err, ctag="0", type_="M", verb="DENY"):
        return "{}\r\n{}{}\r\n{}{}\r\n;\r\n".format(
            cls.header(node_name, ctag, type_, verb),
            cls.TAB,
            err,
            cls.TAB,
            cls.ERRORS[err],
        )

    @classmethod
    def generate(cls, entries, tid, ctag, type_="M"):
        """
        Response generator returns str
        """
        # Randomly allocate entries to pages
        pages = []
        while entries:
            num_entries = randint(1, min(len(entries), cls.ENTRIES_PRE_PAGE))
            pages.append([])
            while num_entries > 0:
                pages[-1].append(entries.pop(0))
                num_entries -= 1

        ret = ""
        for idx, page in enumerate(pages):
            ret += TL1Response.header(tid, ctag) + "\r\n"
            for entry in page:
                ret += "{}\"{}\"\r\n".format(cls.TAB, str(entry))

            # Page termination
            if idx == len(pages) - 1:
                ret += ";\r\n"
            else:
                ret += ">\r\n\r\n"

        return ret


class TL1CommandProcessor(BaseCommandProcessor):

    LOGGED_OUT_COMMANDS = {"ACT-USER"}

    def __init__(self, node_name, config=None):
        super(TL1CommandProcessor, self).__init__()
        self.node_name = node_name
        self.config_processor = config
        self._motd_shown = False
        self._authed = None

    def parse_kwargs(self, kwargs, strict=True):
        parts = kwargs.split(",")
        result = {}
        for p in parts:
            try:
                kv = p.split("=")
                if len(kv) == 2:
                    result[kv[0]] = kv[1]
                else:
                    result[kv[0]] = None
            except ValueError:
                self.logger.error("Failed to parse kwarg: {}".format(p))
                if strict:
                    raise

    @staticmethod
    def aid_is_all(aid):
        """ Return True if the given aid should be treated like 'ALL'"""
        return not aid or aid == "ALL"

    def parse_and_execute_command(self, line):
        """
        OVERRIDE: To handle empty lines

        Process non-empty lines using whichever method is returned
        by ``get_command_func``
        """
        # Empty command is not allowed in TL1
        if not line.strip():
            self.error("IITA")
            return True

        func, args = self.get_command_func(line)
        if not func:
            self.logger.debug("%s can't process : %s, falling back to parent" % (self.__class__.__name__, line))
            return False
        else:
            func(*args)
        return True


    def get_command_func(self, line):
        """
        OVERRIDE: to handle TL1 format

        Look into the Processor to find a method matching the given
        command/line:

        - RTRV-EQPT:::1; -> do_rtrv_eqpt()
        """

        line_split = line.strip().split(":")
        # No TID
        if len(line_split) == 1:
            return self.error, ["IITA"]
        # Not enough cols
        if len(line_split) < 4:
            return self.error, ["IBMS"]
        # Missing ctag (empty column)
        if not line_split[3]:
            return self.error, ["IICT"]

        command, tid, aid, ctag = line_split[:4]

        # Sanitize:
        # 1. quotes not allowed in ctag
        if '"' in ctag:
            return self.error, ["IICT"]
        # 2. Quotes in tid or aid are ignored
        tid = tid.strip('"')

        # Check Auth
        if not self._authed and command not in self.LOGGED_OUT_COMMANDS:
            return self.error, ["PLNA", ctag]


        args = []
        if len(line_split) > 4:
            # Strip quotes from these args
            args = [s.strip('"') for s in line_split[4:6]]

        kwargs = []
        if len(line_split) > 6:
            kwargs = line_split[6:]

        func = "do_" + command.replace("-", "_").lower()
        self.logger.info(
            "exec tokens: f={}, t={}, aid={}, c={}, arg={}, kwarg={}".format(
                func, tid, aid, ctag, args, kwargs
            )
        )
        return getattr(self, func, None), [tid, aid, ctag, args, kwargs]

    def get_prompt(self):
        if not self._motd_shown:
            self._motd_shown = True
            return  self._MOTD + "\r\n< "
        return "< "

    def error(self, err, ctag="0", type_="M", verb="DENY"):
        self.write(str(
            TL1Response.error(self.node_name, err, ctag, type_, verb)
        ))

    def do_rtrv_eqpt(self, tid, aid, ctag, args, kwargs):
        entries = []
        for chassis in self.switch_configuration.chassis_table.values():
            for card in chassis.card_table.values():
                card_aid = card.get_full_aid()
                if not self.aid_is_all(aid) and not card_aid.startswith(aid):
                    continue

                entries.append(
                    TL1Entry(
                        aid=card_aid,
                        type_="",
                        fields=card.fields,
                        statuses=card.statuses,
                    )
                )

        self.write(TL1Response.generate(entries, tid, ctag))

    def do_act_user(self, tid, aid, ctag, args, kwarg):
        """
        ;
        < ACT-USER:"TID":"urban":1::;

           "TID" 20-12-29 10:07:13
        M  1 COMPLD
           /*AUTHTYPE=PRIMARY*/
        ;
        <

        """
        if len(args) != 2:
            return self.error("IPMS", ctag)

        pwd = args[1]
        if not pwd:
            return self.error("IPMS", ctag)

        # Store the current user
        self._authed = aid

        time.sleep(1)
        resp = TL1Response.header(tid, ctag, verb="COMPLD")
        resp += "\r\n{}{}\r\n;\r\n".format(TL1Response.TAB, "/*AUTHTYPE=FAKE*/")
        self.write(resp)

    def do_canc_user(self, tid, aid, ctag, args, kwarg):
        """
        < CANC-USER:"TID":"urban":1;

           "TID" 20-12-29 10:10:42
        M  1 COMPLD
        ;
        """
        self._authed = None
        self.write(TL1Response.header(tid, ctag, verb="COMPLD") + "\r\n;\r\n")



    _MOTD = """

This computer system may be accessed only by authorized users.
The data and programs in this system are private, proprietary,
confidential and protected by copyright law and international
treaties. Unauthorized access, use, knowledge, duplication,
reproduction, modification, distribution, retransmission,
download or disclosure of any of the data and programs in this
system or any portion of it may result in severe civil and
criminal penalties and will be enforced and prosecuted to the
maximum extent possible under law. Employees or other Company
authorized users exceeding their authorizations subject
themselves to Company initiated disciplinary proceedings.

--- Copyright (c) 2000 - 2020 Ciena (R) Corporation. All Rights Reserved ---
|  NOTICE: This is a private computer system.                              |
|  Unauthorized access or use may lead to prosecution.                     |
|                                                                          |
|  Ciena 6500-7 PACKET-OPTICAL                                             |
----------------------------------------------------------------------------

/*
 * Starting Interactive TL1 Command Mode.
 * Type ? for help while constructing TL1 commands.
 * Type .? for specific parameter/keyword help.
 */

"""
