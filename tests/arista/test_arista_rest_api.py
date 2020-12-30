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
import unittest

import pyeapi
from hamcrest import assert_that, is_
from pyeapi.api.vlans import Vlans
from pyeapi.eapilib import CommandError

from tests.arista import with_eapi
from tests.util.global_reactor import TEST_SWITCHES
from tests.util.protocol_util import ProtocolTest


class TestAristaRestApi(ProtocolTest):
    _tester = None
    test_switch = "arista"

    @with_eapi
    def test_get_vlan(self, node):
        result = node.api("vlans").get(1)

        assert_that(
            result,
            is_(
                {"name": "default", "state": "active", "trunk_groups": [], "vlan_id": 1}
            ),
        )

    @with_eapi
    def test_execute_show_vlan(self, node):
        result = node.connection.execute("show vlan")

        assert_that(
            result,
            is_(
                {
                    "id": AnyId(),
                    "jsonrpc": "2.0",
                    "result": [
                        {
                            "sourceDetail": "",
                            "vlans": {
                                "1": {
                                    "dynamic": False,
                                    "interfaces": {},
                                    "name": "default",
                                    "status": "active",
                                }
                            },
                        }
                    ],
                }
            ),
        )

    @with_eapi
    def test_execute_show_vlan_unknown_vlan(self, node):
        with self.assertRaises(CommandError) as expect:
            node.connection.execute("show vlan 999")

        assert_that(
            str(expect.exception),
            is_(
                "Error [1000]: CLI command 1 of 1 'show vlan 999' failed: could not run command "
                "[VLAN 999 not found in current VLAN database]"
            ),
        )

        assert_that(
            expect.exception.output,
            is_(
                [
                    {
                        "vlans": {},
                        "sourceDetail": "",
                        "errors": ["VLAN 999 not found in current VLAN database"],
                    }
                ]
            ),
        )

    @with_eapi
    def test_execute_show_vlan_invalid_input(self, node):
        with self.assertRaises(CommandError) as expect:
            node.connection.execute("show vlan shizzle")

        assert_that(
            str(expect.exception),
            is_(
                "Error [1002]: CLI command 1 of 1 'show vlan shizzle' failed: invalid command "
                "[Invalid input]"
            ),
        )

    @with_eapi
    def test_add_and_remove_vlan(self, node):
        result = Vlans(node).configure_vlan("737", ["name wwaaat!"])
        assert_that(result, is_(True))

        result = Vlans(node).delete("737")
        assert_that(result, is_(True))


class AnyId(object):
    def __eq__(self, o):
        try:
            int(o)
        except ValueError:
            return False

        return True
