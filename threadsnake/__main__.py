"""
Basic python minifier, meant for script packing.

When merging multiple files, this can break your code.
"""
import argparse
import os
from threadsnake import ThreadSnake


def main():
    a = ThreadSnake()
    parser = argparse.ArgumentParser(description='Minify Python Scripts')
    parser.add_argument('--no-compress', action='store_true')
    parser.add_argument('--no-rename', action='store_true')
    parser.add_argument('files', nargs='+')
    args = parser.parse_args()
    a = ThreadSnake(no_compress=args.no_compress, no_rename=args.no_rename)
    for file in args.files:
        module_name = os.path.basename(file).split('.')[0]
        with open(file, 'r') as f:
            a.add(f.read(), module_name)
    a.apply()
    print(a.pack())


if __name__ == "__main__":
    main()
