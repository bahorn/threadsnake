"""
Basic python minifier, meant for script packing.

When merging multiple files, this can break your code.
"""
import argparse
import os
from threadsnake import ThreadSnake


def main():
    parser = argparse.ArgumentParser(description='Minify Python Scripts')
    parser.add_argument('--no-compress', action='store_true')
    parser.add_argument('--rename', action='store_true')
    parser.add_argument('--rfilter')
    parser.add_argument('files', nargs='*')
    args = parser.parse_args()

    regex = [] if args.rfilter is None else [args.rfilter]

    ts = ThreadSnake(
        no_compress=args.no_compress,
        no_rename=not args.rename,
        regex=regex
    )

    for file in args.files:
        module_name = os.path.basename(file).split('.')[0]
        with open(file, 'r') as f:
            ts.add(f.read(), module_name)
    ts.apply()

    print(ts.pack())


if __name__ == "__main__":
    main()
