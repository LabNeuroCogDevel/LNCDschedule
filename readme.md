# LNCD scheduler (DB management)

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
 `ln -s hooks/pre-commit  .git/hooks/pre-commit`

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

