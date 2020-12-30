
.PHONY: all help tests black usort


help:
	@echo "fake-switches helper:"
	@echo ""
	@echo " - fmt: Format the code (including tests) = black + usort"
	@echo " - black: Run code formatter"
	@echo " - usort: Run import formatter"
	@echo " - tests: Run all tests in lowest verbosity"
	@echo ""
	@echo "Internal/advanced:"
	@echo ""
	@echo " - fmt_test: Ensure no files need formatting"
	@echo " - clean: Remove all .pyc filesnd tox envs"
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


fmt_test:
	@echo " * Checking code format - this will fail if any file needs formatting"
	@black --check fake_switches/ tests/
	@usort check fake_switches/ tests/


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
	rm -fr .venv/ .tox/
