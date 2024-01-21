#!/usr/bin/env bash

# local directory is SCRIPT_DIR
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate the virtualenv
source "./venv/bin/activate"

# Run the app
./venv/bin/python app.py