#!/bin/sh

cat $(dirname $(realpath "$0"))/../pyproject.toml | grep "version = " | cut -d'"' -f 2
