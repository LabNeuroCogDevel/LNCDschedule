# non-file targets
.PHONY: create-env install clean lint test coverage-report binary all
# no built in rules
.SUFFIXES:
MAKEFLAGS += --no-builtin-rules

# debian is still default python2
PYTHONAPP = python3 -m 
# files that, if changed, would need to rerun coverage/test/compile
PYTHONCODE = $(wildcard *.py)
CODEFILES = $(PYTHONCODE) $(wildcard ui/*.ui)

# files behind non-file targets
# first is default action 'make' => test
test: coverage-report .QA/test-results.txt
all: test lint
create-env: env/bin/activate
lint: .QA/lint-res.txt
coverage-report: .coverage 
binary: dist/schedule/schedule/schedule.py

env/bin/activate:
	$(PYTHONAPP) venv env
	@echo 'Run: source env/bin/activate'

install: env/bin/activate
	# dont run if we dont have VIRTUAL_ENV
ifdef VIRTUAL_ENV
else
	$(error ERROR: first you must 'source env/bin/activate')
endif
	$(PYTHONAPP) pip install --upgrade pip
	$(PYTHONAPP) pip install -r requirements.txt
	mkdir .QA

clean:
	@echo 'cleaning'
	rm -rf .coverage htmlcov/

.QA/lint-res.txt: $(PYTHONCODE)
	$(PYTHONAPP) pylint $(PYTHONCODE) --extension-pkg-whitelist=PyQt5 | tee $@

.QA/test-results.txt: $(CODEFILES)
	$(PYTHONAPP) pytest tests -v | tee $@

.coverage: $(CODEFILES) 
	make clean
	find . -name '*.py' -not -path './env/*' -not -path './tests/*' -exec $(PYTHONAPP) coverage run {} +
	$(PYTHONAPP) coverage report

img/schedule.ico: img/schedule_icon.png
	convert img/schedule_icon.png img/schedule.ico

dist/schedule/schedule/schedule.py: $(CODEFILES)
	rm -r build/ dist/
	pyinstaller --add-data 'config.ini;.' --add-data 'LunaIntraDB-c4b5278b4e6c.p12;.' --add-data 'queries.sql;.' --add-data 'ui/;ui/'  -y -i img/schedule.ico schedule.py 

dist/schedule/schedule: dist/schedule/schedule/schedule.py
	rm -r /l/bea_res/Applications/schedule
	cp -r dist/schedule/ /l/bea_res/Applications/
	
