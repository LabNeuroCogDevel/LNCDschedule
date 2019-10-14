.PHONY: create-env
create-env:
	python3 -m venv env
	@echo 'Run: source env/bin/activate'

.PHONY: install
install:
	pip install --upgrade pip
	pip install -r requirements.txt

.PHONY: clean
clean:
	@echo 'cleaning'
	rm -rf .coverage htmlcov/

.PHONY: Pipfile
Pipfile:
	pipenv install PyQt5 pyesql psycopg2 'git+https://github.com/LabNeuroCogDevel/LNCDcal.py#egg=9592386' pyOpenSSL pytest-qt

.PHONY: lint
lint: clean
	pylint schedule.py --extension-pkg-whitelist=PyQt5

.PHONY: test
test: clean
	python3 -m pytest tests -v
	find . -name '*.py' -exec coverage run {} +

.PHONY: coverage-report
coverage-report:
	coverage report

img/schedule.ico: img/schedule_icon.png
	convert img/schedule_icon.png img/schedule.ico

dist/schedule/schedule:
	rm -r build/ dist/
	pyinstaller --add-data 'config.ini;.' --add-data 'LunaIntraDB-c4b5278b4e6c.p12;.' --add-data 'queries.sql;.' --add-data 'ui/;ui/'  -y -i img/schedule.ico schedule.py 
dist/schedule/schedule: dist/schedule/schedule/schedule.py
	rm -r /l/bea_res/Applications/schedule
	cp -r dist/schedule/ /l/bea_res/Applications/
	
