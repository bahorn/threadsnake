"""
Basic python minifier, meant for script packing.

When merging multiple files, this can break your code.
"""
import sys
import os
from threadsnake import ThreadSnake


def main():
    a = ThreadSnake()
    for file in sys.argv[1:]:
        module_name = os.path.basename(file).split('.')[0]
        with open(file, 'r') as f:
            a.add(f.read(), module_name)
    a.apply()
    print(a.pack())


if __name__ == "__main__":
    main()
