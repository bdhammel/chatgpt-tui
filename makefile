clean-src:
	autoflake --in-place --remove-unused-variables ai/*.py
	isort ai/
	black ai/
	flake8 ai/

clean-tests:
	autoflake --in-place --remove-unused-variables tests/*.py
	isort tests/
	black tests/
	flake8 tests/

clean: clean-src clean-tests

test: clean
	mypy ai/
	pytest
