from ast import parse, _Unparser, Module
import zlib
import base64
import builtins
from passes import \
        RemoveDocstrings, \
        CleanImports, \
        RemoveImports, \
        RenameVariables


def ts_unparse(ast_obj):
    unparser = _Unparser()
    return unparser.visit(ast_obj)


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

    def __init__(self, no_compress=False, no_rename=False):
        self._root = parse('').body
        self._perfile_passes = [
            RemoveDocstrings(),
        ]
        self._passes = [
            CleanImports(),
            RemoveImports()
        ]

        if not no_rename:
            self._passes.append(RenameVariables())

        self._cfg = {
            'RemoveImports': {
                'remove': ['']
            },
            'RenameVariables': {
                'banned':
                    list(globals().keys()) + list(builtins.__dict__.keys())
            }
        }
        self._no_compress = no_compress

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
        self._root += curr.body

        if module_name is not None:
            self._cfg['RemoveImports']['remove'].append(module_name)

    def apply(self):
        """
        Run the code over the collective AST
        """
        curr = Module()
        curr.body = self._root
        curr = self.apply_passes(curr, self._passes)

        self._root = curr

    def pack(self):
        """
        Get a minified string representation of the program.
        """
        file = ts_unparse(self._root.body)
        if self._no_compress:
            return file
        return compress_pack(file)
