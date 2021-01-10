import logging
import string

from twisted.conch.insults import insults

from fake_switches.ciena.c6500.command_processor.tl1 import (
    TL1CommandProcessor,
    TL1Response,
)
from fake_switches.command_processing.piping_processor_base import PipingProcessorBase
from fake_switches.command_processing.shell_session import ShellSession
from fake_switches.switch_core import SwitchCore
from fake_switches.terminal import LoggingTerminalController
from fake_switches.terminal.ssh import SshTerminalController
from fake_switches.terminal.ssh import SwitchSSHShell


class CienaTL1Shell(insults.TerminalProtocol):
    """
    Ciena TL1 terminal is pretty thik (special)... "

    - arrows do not work (they print garbage)
    - Insert mode makes no sense
    - Ctrl+D exits
    - Tab does nothing
    - Enter is swallowed (TL1 behaviour)
    - Any lower case characters that are unquoted will become uppercase
    - Inject TID if left empty
    """

    _printableChars = string.printable.encode("ascii")
    _log = logging.Logger("CienaTL1TerminalController")

    def __init__(self, user, switch_core):
        self.user = user
        self.switch_core = switch_core
        self.session = None
        self.awaiting_keystroke = None
        self._quoted = False

        # TID ready to be displayed (quoted)
        self.tid = switch_core.switch_configuration.node_name
        if not self.tid.isupper():
            self.tid = '"{}"'.format(self.tid)
        self.tid = self.tid.encode("utf8")

    def connectionMade(self):
        # A list containing the characters making up the current line
        self.lineBuffer = []
        self.lineBufferIndex = 0

        t = self.terminal

        # A map of keyIDs to bound instance methods.
        self.keyHandlers = {
            t.BACKSPACE: self.handle_BACKSPACE,
            b";": self.handle_SEMI,
            b"\x04": self._exit,
            # glitches
            t.DELETE: None,  # [3~
            t.INSERT: None,  # [2~
            t.HOME: None,  # [H
            t.END: None,  # [F
            t.PGUP: None,  # [5~
            t.PGDN: None,  # [6~
            t.LEFT_ARROW: None,  # [C
            t.RIGHT_ARROW: None,  # [D
            t.UP_ARROW: None,  # [A
            t.DOWN_ARROW: None,  # [B
            # NO-OPs
            t.TAB: self._blackhole,
            b"\r": self._blackhole,
            b"\n": self._blackhole,
        }

        self.session = self.switch_core.launch(
            "ssh+tl1", SshTerminalController(shell=self)
        )

    def _blackhole(self):
        pass

    def _exit(self):
        # TODO: Check session is not logged in!
        self.terminal.loseConnection()

    def handle_BACKSPACE(self):
        if not self.lineBuffer:
            return

        if self.lineBuffer[-1] == b'"':
            self._quoted = not self._quoted

        if not self._is_echo_off():
            self.terminal.cursorBackward()
            self.terminal.deleteCharacter()

        del self.lineBuffer[-1]

    def handle_SEMI(self):
        self.terminal.write(b";")
        line = b"".join(self.lineBuffer)
        self.lineBuffer = []
        self.terminal.nextLine()
        self.lineReceived(line)

    def keystrokeReceived(self, keyID, modifier):
        m = self.keyHandlers.get(keyID)
        if m is not None:
            m()
        elif keyID in self._printableChars:
            self.characterReceived(keyID, False)
        else:
            self._log.warn("Received unhandled keyID: {keyID!r}".format(keyID=keyID))

    def _is_echo_off(self):
        """
        Echo is off only in password prompt:

            ACT-USER::"urban":1::<pwd>
        """
        sline = b"".join(self.lineBuffer).strip(b" ")
        return len(sline) > 7 and sline[0:8] == b"ACT-USER" and sline.count(b":") == 5

    def characterReceived(self, ch, moreCharactersComing):
        if ch == b'"':
            self._quoted = not self._quoted

        if not self._quoted:
            ch = ch.upper()

        sline = b"".join(self.lineBuffer).strip(b" ")
        if ch == b":" and self.lineBuffer.count(b":") == 1 and not sline.split(b":")[1]:
            self.terminal.write(self.tid)
            self.lineBuffer.extend(self.tid.split())

        if not self._is_echo_off():
            self.terminal.write(ch)

        self.lineBuffer.append(ch)

    def unhandledControlSequence(self, seq):
        self._log.warning("Unhandled control seq: {}".format(seq))

    def lineReceived(self, line):
        line = line.decode()
        still_listening = self.session.receive(line)
        if not still_listening:
            self.terminal.loseConnection()


class BaseCiena6500Core(SwitchCore):
    def __init__(self, switch_configuration):
        super(BaseCiena6500Core, self).__init__(switch_configuration)
        self.last_connection_id = 0
        self.logger = logging.getLogger(
            "fake_switches.ciena.%s" % self.switch_configuration.node_name
        )

    def launch(self, protocol, terminal_controller):
        self.last_connection_id += 1
        self.logger = logging.getLogger(
            "fake_switches.ciena.%s.%s.%s"
            % (self.switch_configuration.node_name, self.last_connection_id, protocol)
        )

        self.logger.debug("Starting new '{}' session".format(protocol))
        if self.switch_configuration.mode == "cli":
            processor = self.new_cli_processor()
        elif self.switch_configuration.mode == "tl1":
            processor = self.new_tl1_processor()
        else:
            raise ValueError("launch: Unsupported protocol {}".format(protocol))

        processor.init(
            self.switch_configuration,
            LoggingTerminalController(self.logger, terminal_controller),
            self.logger,
            PipingProcessorBase(self.logger),  # FIXME(urban): using default for now
        )

        return CienaShellSession(processor)

    def new_cli_processor(self):
        raise NotImplementedError()

    def new_tl1_processor(self):
        return TL1CommandProcessor(node_name=self.switch_configuration.node_name)

    def get_netconf_protocol(self):
        return None

    def get_protocol_shell(self, variant):
        """
        Return a normal ssh session for "cli" and a TL1 for "tl1" variant
        """
        self.logger.info("Ciena requested variant: {}".format(variant))
        return {
            "cli": SwitchSSHShell,
            "tl1": CienaTL1Shell,
        }.get(variant, SwitchSSHShell)

    @staticmethod
    def get_default_ports():
        """ No default ports here... """
        return []


class CienaShellSession(ShellSession):
    def handle_unknown_command(self, line):
        self.command_processor.error("ICNV")
