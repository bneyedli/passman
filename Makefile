ENVIRONMENT=dev
PROJECT_VERSION=$(shell poetry version -s)
PROJECT_BUMP_RULE=patch

.git/hooks/pre-commit:
	@pre-commit install

pytype.cfg:
	@pytype --generate-config $@

dist/passman-$(PROJECT_VERSION)-py3-none-any.whl:
	@poetry build

build-dev: dist/passman-$(PROJECT_VERSION)-py3-none-any.whl

install-dev: dist/passman-$(PROJECT_VERSION)-py3-none-any.whl
	@pip install $^

deps-dev: .git/hooks/pre-commit pytype.cfg

version-bump:
	@poetry version $(PROJECT_BUMP_RULE)

git-tag:
	@git commit -a -m "v$$(poetry version -s)"
	@git tag -s "v$$(poetry version -s)" -m "v$$(poetry version -s)"

version: version-bump git-tag

deps: deps-$(ENVIRONMENT)
build: build-$(ENVIRONMENT)
install: install-$(ENVIRONMENT)

.PHONY: deps deps-dev build build-dev install
