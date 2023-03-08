clean:
	isort ai/
	black ai/
	flake8 ai/
	isort tests/
	black tests/
	flake8 tests/

test: clean
	mypy ai/
	pytest
