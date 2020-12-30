
.PHONY: all help tests black usort


help:
	@echo "fake-switches helper:"
	@echo ""
	@echo " - fmt: Format the code (including tests) = black + usort"
	@echo " - black: Run code formatter"
	@echo " - usort: Run import formatter"
	@echo " - tests: Run all tests in lowest verbosity"
	@echo ""


fmt: black usort

black:
	@echo " * Running black"
	@black --diff --safe fake_switches tests


usort:
	@echo " * Running usort"
	@usort diff ./fake_switches/ ./tests/


reqs:
	echo " * Installing requirements (pip install --user)"
	@pip install --user -r ./test-requirements.txt
	@pip install --user -r ./requirements.txt


tests:
	@python3 ./run-tests.py -v 1
