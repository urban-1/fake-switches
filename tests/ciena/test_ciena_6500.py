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

import mock

from tests.util.protocol_util import with_protocol, ProtocolTest


def login(t):
    """
    Utility to login
    """
    t.write('ACT-USER::"urban":1::TEST;')
    t.rread(r".* COMPLD\r")


def close(t):
    t.write_raw("\x04")
    t.read_eof()


class TestCiena6500(ProtocolTest):
    __test__ = True
    test_switch = "ciena6500"

    @with_protocol
    def test_login(self, t):
        login(t)

    @with_protocol
    def test_login_logout(self, t):
        login(t)
        # WARNING: write_raw because:
        # - write, reads back what it wrote
        # - Ciena adds the TID in the command on the fly! What we write
        #   and what we read are not different!
        t.write_raw('CANC-USER::"urban":1;')
        t.rread(r".*COMPLD")

    @with_protocol
    def test_login_ctrl_d(self, t):
        login(t)
        # WARNING: write_raw because:
        # - write, reads back what it wrote
        # - Ciena adds the TID in the command on the fly! What we write
        #   and what we read are not different!
        t.write_raw("\x04")
        t.read_eof()

    @with_protocol
    def test_terminal_adds_tid(self, t):
        t.read_lines_until("< ")
        t.write_raw("RTRV-EQPT:::1;")
        t.read('RTRV-EQPT:"eu-uk-not1-1"::1;')

    @with_protocol
    def test_no_tid_logged_in(self, t):
        login(t)
        t.write_raw("RTRV-EQPT;")
        t.rread(r".*IITA")

    @with_protocol
    def test_not_enough_cols_logged_in(self, t):
        login(t)
        t.write_raw("RTRV-EQPT::;")
        t.rread(r".*IBMS")

    @with_protocol
    def test_no_ctag_logged_in(self, t):
        login(t)
        t.write_raw("RTRV-EQPT:::;")
        t.rread(r".*IICT")

    @with_protocol
    def test_not_logged_in(self, t):
        t.write_raw("RTRV-EQPT:::1;")
        t.rread(r".*PLNA")

    @with_protocol
    def test_no_tid_logged_out(self, t):
        t.write_raw("RTRV-EQPT;")
        t.rread(r".*IITA")

    @with_protocol
    def test_not_enough_cols_logged_out(self, t):
        t.write_raw("RTRV-EQPT::;")
        t.rread(r".*IBMS")

    @with_protocol
    def test_no_ctag_logged_out(self, t):
        t.write_raw("RTRV-EQPT:::;")
        t.rread(r".*IICT")

    @with_protocol
    def test_rtrv_eqpt(self, t):
        login(t)
        t.write_raw("RTRV-EQPT::ALL:1;")
        t.rread(r".*SP-1-15.*")
