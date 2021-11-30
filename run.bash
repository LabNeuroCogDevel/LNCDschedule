#!/usr/bin/env bash
set -e
# install git hook if not already there
test ! -r .git/hooks/pre-commit && ( cd  .git/hooks/; echo ln -s ../../hooks/pre-commit ./; )
pipenv sync
pipenv run ./schedule.py
