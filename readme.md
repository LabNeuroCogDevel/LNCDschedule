# LNCD scheduler (DB management)

## Not tracked
 * `config.ini` configuration settings (db info, cal info)
 * `*.p12` gcal cred file for service account

## Notes

### Database
The database is built elsewhere. Insert and update triggers exist here
  `~/src/db/mdb_psql_clj/resources/sql/triggers.sql`
and the schema is defined here
  `~/src/db/mdb_psql_clj/resources/sql/makedb.sql`


Visit has some confusing views:
 * `visits_view` : json columns full info for visit, no drop info
 * `visits_summary`: most recent note (+ drop values) and action

