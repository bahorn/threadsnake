from ast import parse, _Unparser, Module
import zlib
import base64
from passes import \
        RemoveDocstrings, \
        CleanImports, \
        RemoveImports, \
        RenameVariables, \
        RenameFunctions, \
        RenameClasses


def ts_unparse(ast_obj):
    unparser = _Unparser()
    return unparser.visit(ast_obj)


def compress_pack(src):
    encoded = base64.b85encode(zlib.compress(bytes(src, 'utf-8')))
    script = [
        'import zlib,base64',
        f'exec(zlib.decompress(base64.b85decode({encoded})))'
    ]
    return ';'.join(script)


class ThreadSnake:
    """
    Base class for users.

    This will apply the chosen minifiers over the ast.
    """

    def __init__(self):
        self._root = parse('').body
        self._perfile_passes = [
            RemoveDocstrings(),
        ]
        self._passes = [
            CleanImports(),
            RemoveImports(),
            RenameVariables(),
            RenameFunctions(),
            RenameClasses()
        ]
        self._cfg = {
            'RemoveImports': {
                'remove': ['']
            }
        }

    def add(self, code, module_name=None):
        """
        Add code to the AST
        """
        curr = parse(code)
        for astpass in self._perfile_passes:
            cfg = self._cfg.get(astpass.name())
            if cfg is not None:
                astpass.update_config(cfg)
            curr = astpass.apply(curr)

        self._root += curr.body

        if module_name is not None:
            self._cfg['RemoveImports']['remove'].append(module_name)

    def apply(self):
        curr = Module()
        curr.body = self._root

        for astpass in self._passes:
            cfg = self._cfg.get(astpass.name())
            if cfg is not None:
                astpass.update_config(cfg)
            curr = astpass.apply(curr)

        self._root = curr

    def pack(self):
        """
        Get a minified string representation of the program.
        """
        return ts_unparse(self._root.body)
        #return compress_pack(unparse(self._root.body))
