from ast import parse, unparse
import zlib
import base64
import builtins
from passes import \
        RemoveDocstrings, \
        CleanImports, \
        RemoveImports, \
        RenameVariables, \
        InsertHelpers


DEFAULT_GLOBALS = [
    '__name__',
    '__doc__',
    '__package__',
    '__loader__',
    '__spec__',
    '__annotations__',
    '__builtins__'
]


def compress_pack(src):
    """
    Generate a compressed and executable script from the source code string
    """
    encoded = bytes(src, 'utf-8')
    encoded = zlib.compress(encoded)
    encoded = base64.b85encode(encoded)
    encoded = encoded.decode('ascii')
    script = [
        'import zlib,base64',
        f'exec(zlib.decompress(base64.b85decode("{encoded}")))'
    ]
    return ';'.join(script)


class ThreadSnake:
    """
    Base class for users.

    This will apply the chosen minifiers over the ast.
    """

    def __init__(self, no_compress=False, no_rename=False, regex=None):
        self._root = parse('')
        self._initial_passes = [
            InsertHelpers()
        ]

        self._perfile_passes = [
            RemoveDocstrings(),
        ]
        self._passes = [
            CleanImports(),
            RemoveImports()
        ]

        if not no_rename:
            self._passes.append(RenameVariables())

        # filter this to remove our imports from always being banned.
        banned_str = DEFAULT_GLOBALS + list(builtins.__dict__.keys())
        # Need to add more of these
        # banned_str += dir(set)
        # banned_str += dir(dict)
        # banned_str += dir(list)
        # banned_str += dir(bool)
        # banned_str += dir(int)
        # banned_str += dir(float)
        banned_regex = [] if regex is None else regex

        self._cfg = {
            'RemoveImports': {
                'remove': ['']
            },
            'RenameVariables': {
                'banned_str': banned_str,
                'banned_regex': banned_regex
            }
        }
        self._no_compress = no_compress

        # Now apply the initial passes
        self._root = self.apply_passes(self._root, self._initial_passes)

    def apply_passes(self, code, passes):
        """
        Apply a loop of passess over the code.
        """
        curr = code
        for astpass in passes:
            cfg = self._cfg.get(astpass.name())
            if cfg is not None:
                astpass.update_config(cfg)
            curr = astpass.apply(curr)
        return curr

    def add(self, code, module_name=None):
        """
        Add code to the AST
        """
        curr = parse(code)
        curr = self.apply_passes(curr, self._perfile_passes)
        self._root.body += curr.body

        if module_name is not None:
            self._cfg['RemoveImports']['remove'].append(module_name)

    def apply(self):
        """
        Run the code over the collective AST
        """
        curr = self._root
        curr = self.apply_passes(curr, self._passes)

        self._root = curr

    def pack(self):
        """
        Get a minified string representation of the program.
        """
        file = unparse(self._root.body)
        if self._no_compress:
            return file
        return compress_pack(file)
