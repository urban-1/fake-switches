
!!! WARNING !!!
===============

**Fork of original https://github.com/internap/fake-switches ...** 

**When I started, I had no clue what I was doing :) by the time I was "finished" the 
project looked very very different in some places.**

**Forking because it actually works! But merging to upstream might take a while...
(see an incomplete list of major changes at the end of this doc)**

<hr/>


dev_urban [![Build Status](https://www.travis-ci.com/urban-1/fake-switches.svg?branch=dev_urban)](https://www.travis-ci.com/urban-1/fake-switches)
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
master [![Build Status](https://www.travis-ci.com/urban-1/fake-switches.svg?branch=master)](https://www.travis-ci.com/urban-1/fake-switches)
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
upstream [![Build Status](https://travis-ci.org/internap/fake-switches.svg?branch=master)](https://travis-ci.org/internap/fake-switches)


Fake-switches
=============

![Commandline Demo](demo-cli.gif)

Fake-switches is a pluggable switch/router command-line simulator. It is meant
to help running integrated tests against network equipment without the burden
of having devices in a lab. This helps testing the communication with the
equipment along with all of its layers for more robust high level tests.  Since
it is meant to be used by other systems and not humans, error handling on
incomplete commands and fail-proofing has been mostly left out and only
relevant errors are shown. 

The library can easily be extended to react to some changes in the fake switch
configuration and control an actual set of tools to have an environment
behaving like a real one driven by a switch.  For example, you could hook
yourself to the VLAN creation and use vconfig to create an actual vlan on a
machine for some network testing.

This library is NOT supported by any vendor, it was built by
reverse-engineering network equipment.


Actual supported commands
=========================

Command support has been added in a as-needed manner for the purpose of what
was tested and how.  So see which commands may be used and their supported
behavior, please see the tests section for each model.

| Model   | Protocols        | Test location |
| ------- | ---------------- | ------------- |
| Cisco   | ssh and telnet   | [tests/cisco/test_cisco_switch_protocol.py](tests/cisco/test_cisco_switch_protocol.py) |             
| Brocade | ssh              | [tests/brocade/test_brocade_switch_protocol.py](tests/brocade/test_brocade_switch_protocol.py) |
| Juniper | netconf over ssh | [tests/juniper/juniper_base_protocol_test.py](tests/juniper/juniper_base_protocol_test.py) |
| Dell    | ssh and telnet   | [tests/dell/](tests/dell/) |

Using it with Docker
====================

```shell
$ docker run -P -d internap/fake-switches
$ docker ps
CONTAINER ID        IMAGE                             COMMAND                  CREATED             STATUS              PORTS                     NAMES
6eec86849561        internap/fake-switches            "/bin/sh -c 'fake-swi"   35 seconds ago      Up 13 seconds       0.0.0.0:32776->22/tcp     boring_thompson
$ ssh 127.0.0.1 -p 32776 -l root
root@127.0.0.1's password:  # root
my_switch>enable
Password:  # press <RETURN>
my_switch#show run
Building configuration...

Current configuration : 164 bytes
version 12.1
!
hostname my_switch
!
!
vlan 1
!
interface FastEthernet0/1
!
interface FastEthernet0/2
!
interface FastEthernet0/3
!
interface FastEthernet0/4
!
end

my_switch#

```

Launching with custom parameters
--------------------------------

```shell
$ docker run -P -d -e SWITCH_MODEL="another_model" internap/fake-switches
```

Supported parameters
--------------------

| Name              | Default value     |
| ----------------- | ----------------- |
| SWITCH_MODEL 		| cisco_generic 	|
| SWITCH_HOSTNAME 	| switch 			|
| SWITCH_USERNAME 	| root 				|
| SWITCH_PASSWORD 	| root 				|
| LISTEN_HOST 		| 0.0.0.0 			|
| LISTEN_PORT 		| 22 				|


Building image from source
--------------------------

```shell
$ docker build -t fake-switches .
$ docker run -P -d fake-switches
```

Extending functionality
=======================

The SwitchConfiguration class can be extended and given an object factory with
custom classes that can act upon resources changes. For example :

```python

from twisted.internet import reactor
from fake_switches.switch_configuration import SwitchConfiguration, Port
from fake_switches.transports.ssh_service import SwitchSshService
from fake_switches.cisco.cisco_core import CiscoSwitchCore

class MySwitchConfiguration(SwitchConfiguration):
    def __init__(self, *args, **kwargs):
        super(MySwitchConfiguration, self).__init__(objects_overrides={"Port": MyPort}, *args, **kwargs)


class MyPort(Port):
    def __init__(self, name):
        self._access_vlan = None

        super(MyPort, self).__init__(name)

    @property
    def access_vlan(self):
        return self._access_vlan

    @access_vlan.setter
    def access_vlan(self, value):
        if self._access_vlan != value:
            self._access_vlan = value
            print "This could add vlan to eth0"


if __name__ == '__main__':
    ssh_service = SwitchSshService(
        ip="127.0.0.1",
        ssh_port=11001,
        switch_core=CiscoSwitchCore(MySwitchConfiguration("127.0.0.1", "my_switch", ports=[MyPort("FastEthernet0/1")])))
    ssh_service.hook_to_reactor(reactor)
    reactor.run()
```

Then, if you connect to the switch and do

```
    ssh root@127.0.0.1 -p 11001
    password : root
    > enable
    password:
    # configure terminal
    # vlan 1000
    # interface FastEthernet0/1
    # switchport access vlan 1000
```

Your program should say "This could add vlan to eth0" or do anything you would
want it to do :)


Starting a switch from the command line
=======================================

```shell
    pip install fake-switches
    
    fake-switches

    # On a different shell, type the following:
    ssh root@127.0.0.1 -p 22222
```

Command line help
-----------------

The --help flag is supported.

    fake-switches --help
    usage: fake-switches [-h] [--model MODEL] [--hostname HOSTNAME]
                         [--username USERNAME] [--password PASSWORD]
                         [--listen-host LISTEN_HOST] [--listen-port LISTEN_PORT]

    Fake-switch simulator launcher

    optional arguments:
      -h, --help            show this help message and exit
      --model MODEL         Switch model, allowed values are
                            juniper_qfx_copper_generic, cisco_2960_24TT_L,
                            dell_generic, dell10g_generic, juniper_generic,
                            cisco_2960_48TT_L, cisco_generic, brocade_generic
                            (default: cisco_generic)
      --hostname HOSTNAME   Switch hostname (default: switch)
      --username USERNAME   Switch username (default: root)
      --password PASSWORD   Switch password (default: root)
      --listen-host LISTEN_HOST
                            Listen host (default: 0.0.0.0)
      --listen-port LISTEN_PORT
                            Listen port (default: 2222)


Available switch models
-----------------------

At time of writing this document, the following models are available:
 
  * brocade_generic
  * cisco_generic
  * cisco_2960_24TT_L
  * cisco_2960_48TT_L
  * dell_generic
  * dell10g_generic
  * juniper_generic
  * juniper_qfx_copper_generic

Use the --help flag to find the available models.

The generic models are mainly for test purposes. They usually have less ports than a proper switch
model but behave the same otherwise. Once a "core" is available, more specific models can be very
easily added. Send your pull requests :)


Contributing
============

Feel free raise issues and send some pull request,
we'll be happy to look at them!


Quick Start
-----------


Run locally:

```
$ PYTHONPATH=.:$PYTHONPATH python3 ./fake_switches/cmd/main.py
```

Connect:

```
ssh root@localhost -p 2222
```

Some security config on ssh may disable sha1, in this case run:

```
ssh -oKexAlgorithms=+diffie-hellman-group1-sha1 root@localhost -p 2222
```

Test
----

To run all tests on all environments:

```
tox
```

You can filter tests which is useful when developing. All arguments after `--`
are passed to `nosetests`

```
# Run in one environment only
tox -e py36

# Get some help
$ tox -e py38 -- --help

# Run specific tests down to class-level (not individual test)
tox -e py38 -- --tests tests.ciena

# Filter based on regex - THHIS IS GLITCHY FOR ME
# READ: https://github.com/nose-devs/nose/issues/1045 !!!
# Some commands that did work is (specify test class, filter by test - dif
# not work for py27...):
tox -e py38 -- --tests tests.ciena.test_ciena_6500.TestCiena6500 -m test_login
tox -e py38 -- --tests tests.ciena.test_ciena_6500.TestCiena6500 -m test_login$
tox -e py36 -- --tests tests.ciena.test_ciena_6500 -m 'test_login$'
tox -e py36 -- --tests tests.ciena.test_ciena_6500 -m 'test_.*logged_out'
```


My changes
==========

- WARNING: I have messed with the tests of this project before I figure out how `tox` works :D. 
Turns out that it calls nosetests to run the tests. This is important cause it executes 
setup()/tearDown() in `tests/__init__.py`!!! Because I was running the tests with a custom script
using unittest, I had to hack setUp/tearDown to _not_ rely on a global reactor running all 
switches. Instead, each test now **can** boot its own switch (it doesnt not tho via `tox`) 
- Added --config in main.py and in switch_configuration. This allows me to bootstrap
  devices that are modular in nature - we can specify cards/modules in that config.
    - Add config next to core in SwitchFactory - required
- Added ciena folder aiming for TL1 support on 6500s. For this I needed a new terminal 
  type but most importantly, I needed the same transport layer to support multiple
  "variants". Variant support added to SwitchSshService and is understood by the 
  core_switch which has an opportunity to return different Shell/TerminalProtocol  
    - Allow shell override from core_switch
- Needed a way for ssh (twisted) to not ask username/password. For this I added
  support for username="None" add a free4all auth (fake key-based auth always 
  allowing access)
- Added test runner. As per warning earlier, I changed the tests to 
  spawn one singleton reactor in the run-tests.py but at the same time, each 
  test is spawning its own switch! For this to work, most of the booting code
  has changed:
    - Added SwitchBooter class responsible for turning on and off devices
    - Added config per-service and moved "port" there
    - Removed autoinc next port and replaced it with a "real" next free port based
      on bind()
    - Added some decorators for tests where needed, hacked the existing ones to 
      not be based on config and instead take parameters from core_switch
- Added a Makefile to handle code formating. This is the most disruptive change
  since it touches all of the code... but once your eyes get used to formatted
  code, is hard to live without it
- Added some comments here and there
- Once I reallized I will fork, I changed travis to not have a pypi push step
  since I don't want to accidentaly release a new package :). Did few other 
  tweaks including this doc and changing/upping most versions (python, tox, docker, etc)
- Finally, since this was a 2-3 days pet project and I got impatient... my commit
  messages do not always reflect what is changing :D

My TODO
-------

If I keep on hacking this I would like to do the following:


- [ ] Clean up test code that seems to be from various iterations/generations of the 
  project. Primarily split config from code and reorg a bit utils
- [ ] Checkout docker image and what updates it needs. I also think that we can reduce its size
if we remove not needed build tools after install 
- [ ] Clean up some classes that seem to be very thin (unsure if thats better/possible)
- [ ] Deprecate py27 (does not hurt atm but had to bypass black/usort)
- [ ] Implement Ciena 6500 configurables and more commands
