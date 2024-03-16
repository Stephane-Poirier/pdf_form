#!/bin/zsh

if [ "$1" = "coverage" ]
  then
    shift
    python3 -m coverage run --source=.. -m unittest test_*.py $@
    python3 -m coverage html
    open ./htmlcov/index.html
else
  python3 -m unittest test_*.py $@
fi
