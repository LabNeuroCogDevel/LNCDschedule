#!/usr/bin/env bash
set -euo pipefail
trap 'e=$?; [ $e -ne 0 ] && echo "$0 exited in error"' EXIT

# create test database
#
# 20211129WF - init


DB=lncddb_test
USER=postgres
psqlcmd(){ psql -U $USER "$@"; }

cd $(dirname $0)/../sql
# replace 01_makedb.sql with $DB
echo "drop database if exists $DB; create database $DB;" | psqlcmd
# and then run all the others
ls *sql|grep -v 01_makedb.sql|
   xargs cat | psqlcmd $DB

for f in person.csv ra.txt contact.csv study.csv enroll.csv visit_summary.csv; do
   psqlcmd $DB -c "\\copy ${f//.*/} from '$(pwd)/$f' WITH DELIMITER ',' CSV HEADER ESCAPE E'\\\\';"
done 
