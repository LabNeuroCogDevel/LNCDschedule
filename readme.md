# LNCD scheduler (DB management)

[![Build Status](https://travis-ci.com/LabNeuroCogDevel/LNCDschedule.svg?branch=master)](https://travis-ci.com/LabNeuroCogDevel/LNCDschedule)

Schedule and record visits to the Laboratory of NeuroCognitive Development.

This is unlikely to be too useful to the world at large.
Integrations are specific to the lab's tools (gcal, qualtrics) and firewall. The database schema is tied to internal organization of multimodal experiments with human participates.

Instead see components:
 * google calendar: https://github.com/LabNeuroCogDevel/LNCDcal.py
 * qualtrics - `Qualtrics.py`


## Run without install
 - Mobaxterm/ssh: rhea
 - `schedule.py`

## Install on windows

 - python: https://www.anaconda.com/download/#windows  (install as user, not system)
 - python libaries/dependencies:anaconda navigator -> environments -> root play -> terminal 
    - upmc cert issue: `conda config --set ssl_verify False`
    - version control: `conda install git`
    - LNCDcal: `pip install --trusted-host github.com git+https://github.com/LabNeuroCogDevel/LNCDcal.py`
    - sql: `conda install psycopg2` `pip install pyesql`
    - gui: `conda install pyQt5`
 - app: 
    - anaconda navigator -> projects -> import -> from folder

20190712 - pyqt5 update issue, current fix `pip install pyqt5==5.12.2`
https://github.com/pyinstaller/pyinstaller/issues/4293

### Not tracked (copy)
 * `config.ini` configuration settings (db info, cal info)
 * `*.p12` gcal cred file for service account

## Editing
* `qtcreator` for visual `ui` files (`designer.exe` with anaconda on windows)

## Notes

### Testing
use `make test`, same as `python3 -m pytest`

  * Depends on `pytest`, `pytest-qt` and `pytest-pgsql`
  * within `tests` directory, but expects to be run at root directory (`./sql/` and `./*py` files)
  * makes use of pytest autoloaded `conftest.py` to provided schema loading through shared test fixture `create_db`

using git hooks
 * install: `ln -s $(pwd)/hooks/pre-commit  .git/hooks/pre-commit`
 * ignore: `git commit --no-verify ...`

### Database

Explore with `DBeaver`.


The database is built elsewhere. Insert and update triggers exist here
  `~/src/db/mdb_psql_clj/resources/sql/triggers.sql`
and the schema is defined here
  `~/src/db/mdb_psql_clj/resources/sql/makedb.sql`

These are mirrored in the `sql/` directory.


Visit has some confusing views:
 * `visits_view` : json columns full info for visit, no drop info
 * `visits_summary`: most recent note (+ drop values) and action

