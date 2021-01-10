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

from fake_switches.command_processing.command_processor import CommandProcessor


class BaseCommandProcessor(CommandProcessor):
    def init(
        self, switch_configuration, terminal_controller, logger, piping_processor, *args
    ):
        """
        :type switch_configuration: fake_switches.switch_configuration.SwitchConfiguration
        :type terminal_controller: fake_switches.terminal.TerminalController
        :type logger: logging.Logger
        :type piping_processor: fake_switches.command_processing.piping_processor_base.PipingProcessorBase
        """

        self.switch_configuration = switch_configuration
        self.terminal_controller = terminal_controller
        self.logger = logger
        self.piping_processor = piping_processor
        self.sub_processor = None
        self.continuing_to = None
        self.is_done = False
        self.replace_input = False
        self.awaiting_keystroke = False

    def process_command(self, line):
        """
        Entry point to process commands. This will:

        - Handle pipes
        - Try delegating to subprocessor (if set)
        - Handle "continue_to" actions
        - Execute on this command processor if needed
        - Handle pipe close
        """
        if " | " in line:
            line, piping_command = line.split(" | ", 1)
            piping_started = self.activate_piping(piping_command)
            if not piping_started:
                return False

        processed = False

        if self.sub_processor:
            processed = self.delegate_to_sub_processor(line)

        if not processed:
            if self.continuing_to:
                processed = self.continue_command(line)
            else:
                processed = self.parse_and_execute_command(line)

            if (
                not self.continuing_to
                and not self.awaiting_keystroke
                and not self.is_done
                and processed
                and not self.sub_processor
            ):
                self.finish_piping()
                self.show_prompt()

        return processed

    def parse_and_execute_command(self, line):
        """
        Process non-empty lines using whichever method is returned
        by ``get_command_func``
        """
        if line.strip():
            func, args = self.get_command_func(line)
            if not func:
                self.logger.debug(
                    "%s can't process : %s, falling back to parent"
                    % (self.__class__.__name__, line)
                )
                return False
            else:
                func(*args)
        return True

    def continue_command(self, line):
        """
        Execute the continuing_to action and clear it
        """
        func = self.continuing_to
        self.continue_to(None)
        func(line)
        return True

    def delegate_to_sub_processor(self, line):
        """ Run the line thru subprocessor and close it if it is done """
        processed = self.sub_processor.process_command(line)
        if self.sub_processor.is_done:
            self.sub_processor = None
            self.show_prompt()
        return processed

    def move_to(self, new_processor, *args):
        """
        Handover to a subprocessro and register that subprocessor to this
        processor. All commands will be delegated there until the subprocessor
        sets .is_done = True.
        """
        new_processor.init(
            self.switch_configuration,
            self.terminal_controller,
            self.logger,
            self.piping_processor,
            *args
        )
        self.sub_processor = new_processor
        self.logger.info(
            "new subprocessor = {}".format(self.sub_processor.__class__.__name__)
        )
        self.sub_processor.show_prompt()

    def continue_to(self, continuing_action):
        """
        Allows you to set a func/callable that the next line is going to
        be processed by
        """
        self.continuing_to = continuing_action

    def get_continue_command_func(self, cmd):
        """ FIXME: deprecated/unused """
        return getattr(self, "continue_" + cmd, None)

    def write(self, data):
        """
        Write output to the terminal controller after passing thru
        the pipe (if it is open)
        """
        filtered = self.pipe(data)
        if filtered is not False:
            self.terminal_controller.write(filtered)

    def write_line(self, data):
        self.write(data + u"\n")

    def show_prompt(self):
        if self.sub_processor is not None:
            self.sub_processor.show_prompt()
        else:
            self.write(self.get_prompt())

    def get_prompt(self):
        pass

    def activate_piping(self, piping_command):
        """
        Enable (set on) the piping processor with the given "command"
        For example "begin" or "match" or "include"
        """
        return self.piping_processor.start_listening(piping_command)

    def pipe(self, data):
        """
        Filter the fiven data if the piping_processor is on, else
        return the data as-is
        """
        if self.piping_processor.is_listening():
            return self.piping_processor.pipe(data)
        else:
            return data

    def finish_piping(self):
        """
        Close any piping processor
        """
        if self.piping_processor.is_listening():
            self.piping_processor.stop_listening()

    def on_keystroke(self, callback, *args):
        """
        Register keystroke callback to the terminal controller. This will
        be invoked at any keypress without the user hitting Enter
        """

        def on_keystroke_handler(key):
            self.awaiting_keystroke = False
            self.terminal_controller.remove_any_key_handler()
            callback(*(args + (key,)))

        self.terminal_controller.add_any_key_handler(on_keystroke_handler)
        self.awaiting_keystroke = True
