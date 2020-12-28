# Development

## Setup

```
# Install python headers as per your distro/env
$ sudo dnf install python3-devel

# Install reqs
$ pip install --user -r ./requirements.txt


# Missing dep?!
$ pip install --user service_identity
```

## Run locally

```
$ PYTHONPATH=.:$PYTHONPATH python3 ./fake_switches/cmd/main.py
```

## Connect

```
ssh root@localhost -p 2222
```

Some security config on ssh may disable sha1, in this case run:

```
ssh -oKexAlgorithms=+diffie-hellman-group1-sha1 root@localhost -p 2222
```

## Test

WARNING: Tests are still in py2 :( - NOPE
```
curl "https://bootstrap.pypa.io/get-pip.py" -o "get-pip.py"
python2 ./get-pip.py 
rm ./get-pip.py
pip2 install --user -r ./test-requirements.txt
pip2 install --user -r ./requirements.txt

```

## My changes

- Add --config in main.py
- Add config supporti in switch_configuration
- Add ciena folder 
- Add config next to core in SwitchFactory
- Allow shell override from core_switch
- Add free4all auth with None username!
- Added test runner + changed tests to spawn one singleton reactor
