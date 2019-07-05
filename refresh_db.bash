#!/usr/bin/env bash
cd $(dirname $0)
trap 'e=$?; [ $e -ne 0 ] && echo "$0 exited in error"' EXIT
set -euo pipefail

#
# 20190702 - adapted from from mdb_psql_R repo


[ $# -ne 4 ] && echo "run like: $0 file.sql localhost lncddb 5433 # file host db port" && exit 1
dump_file="$1"; shift
remote_host="$1"; shift
remote_db="$1"; shift
remote_port="$1"; shift

set -x
echo "SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = '$remote_db'
  AND pid <> pg_backend_pid();
drop database if exists $remote_db;create database $remote_db;" | psql -U postgres -h $remote_host -p $remote_port
cat $dump_file | psql -U postgres -h $remote_host -p $remote_port $remote_db 
cat sql/roles.sql | psql -U postgres -h $remote_host -p $remote_port $remote_db
echo "EDIT ME: add trust line to config file: "
psql -U postgres -h $remote_host -p $remote_port $remote_db -c "SHOW hba_file;"
