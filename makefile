clean:
	isort ai/
	black ai/
	flake8 ai/
	mypy ai/
