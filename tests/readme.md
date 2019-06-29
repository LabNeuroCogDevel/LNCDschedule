# Testing

* tests are expected to be run from project root directory. imports are relative to there. see `make test` at the top level.
* pytest finds all files like `test_*py` in this and all sub folders. The two files that don't match aid in testing:
  * `pyesql_helper.py` - class to mock out pyesql briding `execute()` and `cursor()`
  * `conftest.py` - fixtures `create_db` and `lncdapp` 


