#!/bin/sh
cat $1 | wc
python3 ./threadsnake/ $1| wc
python3 ./threadsnake/ $1 | python3
