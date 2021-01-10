
.PHONY: all help tests black usort


help:
	@echo "fake-switches helper:"
	@echo ""
	@echo " - fmt: Format the code (including tests) = black + usort"
	@echo " - tests: Run all tests in lowest verbosity"
	@echo ""
	@echo "Internal/advanced:"
	@echo ""
	@echo " - black: Run code formatter"
	@echo " - usort: Run import formatter"
	@echo " - fmt_check: Ensure no files need formatting"
	@echo " - clean: Remove all .pyc files"
	@echo " - distclean: Remove all .pyc + eggs/dist/build"
	@echo " - maintclean: Remove all .pyc + eggs/dist/build + venv/tox/src"
	@echo " - keys: NOT WORKING - regenerate ssh keys for twisted ssh"
	@echo ""


fmt: black usort


black:
	@echo " * Running black"
	@black --safe fake_switches/ tests/


usort:
	@echo " * Running usort"
	@usort format fake_switches/ tests/


reqs:
	@echo " * Installing requirements (pip install --user)"
	@pip install --user -r ./test-requirements.txt
	@pip install --user -r ./requirements.txt


fmt_check:
	@echo " * Checking code format - this will fail if any file needs formatting"
	@black --check fake_switches/ tests/ || { echo "Skipping black (py<3.6)"; }
	@usort check fake_switches/ tests/ || { echo "Skipping usort (py<3.6)"; }


tests: fmt_test
	@echo " * Starting tests"
	# @python3 ./run-tests.py -v 1
	tox


clean:
	@find . -name "*.pyc" -exec rm -f {} \;
	@find . -name '__pycache__' -type d | xargs rm -fr


distclean: clean
	rm -fr *.egg *.egg-info/ .eggs/ dist/ build/


maintclean: distclean
	rm -fr .venv/ .tox/ ./src


keys:
	ssh-keygen -f /tmp/fake -t rsa -b 2048 -C fake@ssh -N '' <<<y 2>&1 >/dev/null
	cp /tmp/fake /tmp/fake.pub ./fake_switches/transports/keys
