# non-file targets
.PHONY: install clean lint test coverage-report binary all lncddb_test
# no built in rules
.SUFFIXES:
MAKEFLAGS += --no-builtin-rules

# using pipenv by default. but can still use python
# 'python3 -m' for pytest and to be extra cautious w/ execs
PYTHONAPP := $(shell command -v pipenv 2> /dev/null)
ifndef PYTHONAPP
	PYTHONAPP := python3 -m
endif

# files that, if changed, would need to rerun coverage/test/compile
PYTHONCODE = $(wildcard *.py table/*.py)
CODEFILES = $(PYTHONCODE) $(wildcard ui/*.ui)
TESTS = $(wildcard tests/**)

# files behind non-file targets
# first listed here is default action run by 'make' w/o args (=> test)
test: .QA/test.txt
all: test lint coverage-report
coverage-report: .QA/coverage.txt
lint: .QA/lint.txt
binary: dist/schedule/schedule/schedule.py
lncddb_test: sql/*csv
	scripts/fake_db.bash
clean:
	find . -name __pycache__ -type d -exec rm {} \+
.QA:
	mkdir .QA

.git/hooks/pre-commit:
	cd .git/hooks && ln -s ../../scripts/pre-commit ./

.git/hooks/pre-push:
	cd .git/hooks && ln -s ../../scripts/pre-push ./

install_local: requirements.txt | .QA .git/hooks/pre-commit .git/hooks/pre-push
	$(PYTHONAPP) pip install --upgrade pip
	$(PYTHONAPP) pip install -r requirements.txt

install: Pipfile | .QA .git/hooks/pre-commit .git/hooks/pre-push
	@echo also see make install_local to use requirements.txt
	pipenv install --dev # --site-packages

.QA/lint.txt: $(PYTHONCODE) | .QA
	$(PYTHONAPP) pylint $(PYTHONCODE) --extension-pkg-whitelist=PyQt5 | tee $@

.QA/test.txt: $(CODEFILES) $(TESTS) | .QA
	scripts/tests_xvfb | tee $@

.QA/coverage.txt: $(CODEFILES)  | .QA
	$(PYTHONAPP) coverage erase
	# N.B. see .coveragerc, '-' means don't stop if test fails
	- $(PYTHONAPP) coverage run -m pytest
	$(PYTHONAPP) coverage report

# used from Windows (with `/l` mnt point) to provide .exe
img/schedule.ico: img/schedule_icon.png
	convert img/schedule_icon.png img/schedule.ico

dist/schedule/schedule/schedule.py: $(CODEFILES)
	rm -r build/ dist/
	pyinstaller --add-data 'config.ini;.' --add-data 'LunaIntraDB-c4b5278b4e6c.p12;.' --add-data 'queries.sql;.' --add-data 'ui/;ui/'  -y -i img/schedule.ico schedule.py

dist/schedule/schedule: dist/schedule/schedule/schedule.py
	rm -r /l/bea_res/Applications/schedule
	cp -r dist/schedule/ /l/bea_res/Applications/

