#!/usr/bin/env bash
set -e
pipenv sync
pipenv run ./schedule.py
