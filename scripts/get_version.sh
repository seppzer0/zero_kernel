#!/bin/sh
#
# This is an SH version of get_version.py, usually used for cases when Python interpreter is unavailable.
#

cat $(dirname $(realpath "$0"))/../pyproject.toml | grep "version = " | cut -d'"' -f 2
