import sys
import os
MAGIC_CONST = 1000


class Pointless:
    access_this = 'bbbbbb'


class Test(Pointless):
    """
    doc string
    """

    def __init__(self, var):
        self._blah = MAGIC_CONST * (var + 100)

    def fun(self):
        return self._blah * self._blah

    def get(self):
        return self.access_this


def main():
    cool = Test(MAGIC_CONST)
    print(os.system('cat /etc/hosts'))
    print(f'{cool.fun()}')
    sys.path
    print(sys.path[0].split('/')[-1])
    print(int('1337'))
    print(cool.get())


if __name__ == "__main__":
    main()
