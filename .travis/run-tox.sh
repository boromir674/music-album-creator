#!/bin/bash

set -e
set -u

export TOX_SKIP_MISSING_INTERPRETERS="False";

tox

coveralls