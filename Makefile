.PHONY: test lint

test:
	python3 -m pytest

Pipfile:
	pipenv install PyQt5 pyesql psycopg2 'git+https://github.com/LabNeuroCogDevel/LNCDcal.py#egg=9592386' pyOpenSSL pytest-qt

dist/schedule/schedule:
	python3 -m pyinstall schedule.py
lint:
	pylint schedule.py --extension-pkg-whitelist=PyQt5
