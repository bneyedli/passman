PROJECT_VERSION=$(shell poetry version -s)

.git/hooks/pre-commit:
	@pre-commit install

requirements.txt:
	@poetry export -o requirements.txt

deps: requirements.txt .git/hooks/pre-commit pytype.cfg
	@pip install -r $^

dist/passman-$(PROJECT_VERSION)-py3-none-any.whl:
	@poetry build

build: dist/passman-$(PROJECT_VERSION)-py3-none-any.whl

install: dist/passman-$(PROJECT_VERSION)-py3-none-any.whl
	@pip install $^
