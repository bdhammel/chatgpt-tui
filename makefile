clean:
	isort ai/
	black ai/
	flake8 ai/

test: clean
	mypy ai/
