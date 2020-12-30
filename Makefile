
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
	@echo ""


fmt: black usort


black:
	@echo " * Running black"
	@black --safe fake_switches/ tests/


usort:
	@echo " * Running usort"
	@usort format fake_switches/ tests/


reqs:
	echo " * Installing requirements (pip install --user)"
	@pip install --user -r ./test-requirements.txt
	@pip install --user -r ./requirements.txt


fmt_test:
	@echo " * Checking code format - this will fail if any file needs formatting"
	@black --check fake_switches/ tests/
	@usort check fake_switches/ tests/


tests: fmt_test
	@echo " * Starting tests"
	@python3 ./run-tests.py -v 1
