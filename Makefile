.PHONY: test lint

Pipfile:
	pipenv install PyQt5 pyesql psycopg2 'git+https://github.com/LabNeuroCogDevel/LNCDcal.py#egg=9592386' pyOpenSSL pytest-qt pytest-pgsql sqlalchemy

lint:
	pylint schedule.py --extension-pkg-whitelist=PyQt5

test:
	python3 -m pytest

img/schedule.ico: img/schedule_icon.png
	convert img/schedule_icon.png img/schedule.ico

dist/schedule/schedule:
	rm -r build/ dist/
	pyinstaller --add-data 'config.ini;.' --add-data 'LunaIntraDB-c4b5278b4e6c.p12;.' --add-data 'queries.sql;.' --add-data 'ui/;ui/'  -y -i img/schedule.ico schedule.py 
dist/schedule/schedule: dist/schedule/schedule/schedule.py
	rm -r /l/bea_res/Applications/schedule
	cp -r dist/schedule/ /l/bea_res/Applications/
	
