lint:
	flake8 --max-line-length 119 --exclude parsetab.py,__pycache__ .

test:
	pytest
