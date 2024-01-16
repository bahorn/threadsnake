#!/bin/bash
RES=`find ./threadsnake/ -depth 1 -name \*.py | xargs python3 ./threadsnake/`
echo "$RES" | wc
echo "$RES" | python3 - ./tests/test2.py
