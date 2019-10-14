# Testing

in the project root directory run `pytest` for all tests, or `pytest --pdb tests/type/test_thing.py` for a single test.

* tests are expected to be run from project root directory. imports are relative to there.
* pytest finds all files like `test_*py` in this and all sub folders. The two files that don't match aid in testing:
  * `pyesql_helper.py` - class to mock out pyesql briding `execute()` and `cursor()`
  * `conftest.py` - fixtures `create_db` and `lncdapp` 


## Setup
in addition to all the application package dependencies (see `Makefile`'s Pipfile section), testing uses pytest and fixtures for postgres and qt
grab

```
python3 -m pip install --user pytest-{qt,pgsql} pdbpp
```


## Running

```bash
# go to project root
cd ~/src/LNCD/LNCDschedule/

# run tests
make test

# OR call pytest directly with debugger on error
python3 -m pytest --pdb

# OR test a single file
python3 -m pytest --pdb tests/db/test_cur_user.py
```

Also see `Makefile` test section and `.travis.yml` script section 

## Developing

pytests `--pdb` option drops into an interactive python shell when an assert fails.

qtbot cannot see dialog/modal windows! https://pytest-qt.readthedocs.io/en/latest/note_dialogs.html. These have to be tested separately. 


useful fixtures:
* `create_db` wires up a mock database. see `tests/db/test_00_insert_update.py`
  * `from pyesql_helper import csv_none` to read a csv with null values into a table . see `tests/db/test_multiRA_insertions.py`
* `lncdapp` creates the main application window and connects a mocked database. see `tests/test_add_visit_and_note.py`
  * `lncdapp.pgtest` is mock database handler (same as `create_db`)
  * when testing a single file be sure to use `APP = QApplication(sys.argv)` at time top. pyQt needs the pointer, otherwise test will fail but give no error message
* use the `qtbot` fixture for window interaction (simulated mouse click, typing)
  * `qtbot.stop()` is useful for pausing a test and visualizing the current state of the GUI
