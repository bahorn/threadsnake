#!/bin/bash
RES=`find ./threadsnake/ -depth 1 -name \*.py | xargs python3 ./threadsnake/ --no-rename`
echo "$RES" | wc
echo "$RES" | python3 - ./testfiles/test2.py
