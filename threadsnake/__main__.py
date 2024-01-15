"""
Basic python minifier, meant for script packing.

When merging multiple files, this can break your code.
"""
from threadsnake import ThreadSnake


def main():
    a = ThreadSnake()
    with open('./threadsnake/output_real.py', 'r') as f:
        a.add(f.read(), 'badmodule')
    a.apply()
    print(a.pack())


if __name__ == "__main__":
    main()
