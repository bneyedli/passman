.git/hooks/pre-commit:
	@pre-commit install

requirements.txt:
	@poetry export -o requirements.txt

deps: requirements.txt .git/hooks/pre-commit pytype.cfg
	@pip install -r $^

