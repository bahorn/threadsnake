"""
Passes we run over the AST
"""
from ast import \
        FunctionDef, \
        ClassDef, \
        AsyncFunctionDef, \
        Module, \
        Constant, \
        Pass, \
        Import, \
        ImportFrom, \
        NodeTransformer, \
        NodeVisitor, \
        Name, \
        Call, \
        Assign, \
        walk, \
        alias, \
        unparse
import copy
from remapnames import map_symbols_to_new_names


def to_module(a):
    m = Module()
    m.body = a
    return m


class ASTPass:
    def __init__(self, cfg={}):
        self._cfg = cfg

    def apply(self, curr_ast):
        return curr_ast

    def update_config(self, cfg):
        self._cfg = cfg

    def name(self):
        return self.__class__.__name__


class RemoveDocstrings(ASTPass):
    TYPES = (FunctionDef, ClassDef, AsyncFunctionDef, Module)

    def apply(self, curr_ast):
        new_ast = copy.deepcopy(curr_ast)
        # https://gist.github.com/phpdude/1ae6f19de213d66286c8183e9e3b9ec1
        for node in walk(new_ast):
            if not isinstance(node, self.TYPES):
                continue

            if not len(node.body):
                continue

            if not hasattr(node.body[0], 'value'):
                continue

            if isinstance(node.body[0], Assign):
                continue

            if not isinstance(node.body[0], Constant):
                continue

            if not isinstance(node.body[0].value.value, str):
                continue

            before = [Pass()] if len(node.body) == 1 else []
            node.body = before + node.body[1:]

        return new_ast


class CleanImports(ASTPass):
    def apply(self, curr_ast):
        """
        Find global imports and move them all into one line, deduping
        """
        # find the global imports
        imports = []
        imports_from = []
        res = []
        for line in curr_ast.body:
            if isinstance(line, Import):
                imports.append(line)
            elif isinstance(line, ImportFrom):
                imports_from.append(line)
            else:
                res.append(line)

        # Dedup the module names
        names = []
        for import_line in imports:
            for name in import_line.names:
                names.append(name.name)
        names = list(map(alias, set(names)))

        # Cleanup ImportFrom
        # Dedup multiple things from the same module
        # remove things that are in the global namespace already

        # Join everything together
        return to_module([Import(names)] + imports_from + res)


class ImportRemover(NodeTransformer):
    def __init__(self, remove):
        self._remove = remove
        super().__init__()

    def visit_Import(self, node):
        new = []
        for name in node.names:
            if name.name not in self._remove:
                new.append(name)
        if len(new) == 0:
            return None

        return Import(new)

    def visit_ImportFrom(self, node):
        for name in self._remove:
            module_name = node.module
            if '.' in module_name and '.' not in name:
                module_name = module_name.split('.')[0]
            if module_name == name:
                return None
        return node


class RemoveImports(ASTPass):
    """
    Remove imports.

    Used if we are combining multiple files together.
    """

    def apply(self, curr_ast):
        if not isinstance(self._cfg, dict):
            return curr_ast

        remove = self._cfg.get('remove')
        if remove is None:
            return curr_ast

        ap = ImportRemover(remove).visit(curr_ast)
        return ap


def add_to_dict(d, v):
    if v not in d:
        d[v] = 0
    d[v] += 1


class FindImportedSymbols(NodeVisitor):
    def __init__(self):
        self._symbols = []

    def symbols(self):
        return self._symbols

    def visit_Import(self, node):
        self._symbols += [name.name for name in node.names]
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        self._symbols += [name.name for name in node.names]
        self.generic_visit(node)


class FindSymbols(NodeVisitor):
    """
    Search the AST for symbols
    Might double visit in a few cases.
    """

    def __init__(self):
        self._counts = {}
        super().__init__()

    def counts(self):
        return self._counts

    def generic_visit(self, node):
        """
        try:
            print(node, unparse(node))
        except:
            print('>')
            pass
        """
        NodeVisitor.generic_visit(self, node)

    def visit_Assign(self, node):
        for target in node.targets:
            if not isinstance(target, Name):
                continue
            add_to_dict(self._counts, target.id)
        self.generic_visit(node)

    def visit_Name(self, node):
        add_to_dict(self._counts, node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node):
        add_to_dict(self._counts, node.attr)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        add_to_dict(self._counts, node.name)
        for arg in node.args.args:
            add_to_dict(self._counts, arg.arg)
        for arg in node.args.kwonlyargs:
            add_to_dict(self._counts, arg.arg)
        if node.args.kwarg:
            add_to_dict(self._counts, node.args.kwarg.arg)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

    def visit_ClassDef(self, node):
        add_to_dict(self._counts, node.name)
        self.generic_visit(node)

    def visit_Lambda(self, node):
        for arg in node.args.args:
            add_to_dict(self._counts, arg.arg)
        self.generic_visit(node)

    def visit_Global(self, node):
        self.visit_Nonlocal(node)

    def visit_Nonlocal(self, node):
        for name in node.names:
            add_to_dict(self._counts, name)
        self.generic_visit(node)


class UpdateSymbols(NodeTransformer):
    def __init__(self, new_syms, modules):
        self._new_syms = new_syms
        self._modules = modules
        super().__init__()

    def visit_Name(self, node):
        new_syms = self._new_syms
        if node.id in new_syms:
            node.id = new_syms[node.id]
        return self.generic_visit(node)

    def visit_Attribute(self, node):
        new_syms = self._new_syms
        for name in unparse(node).split('.'):
            if name in self._modules:
                return node

        if node.attr in new_syms:
            node.attr = new_syms[node.attr]
        return self.generic_visit(node)

    def visit_FunctionDef(self, node):
        new_syms = self._new_syms
        if node.name in new_syms:
            node.name = new_syms[node.name]
        for arg in node.args.args:
            arg.arg = new_syms[arg.arg]
        for arg in node.args.kwonlyargs:
            arg.arg = new_syms[arg.arg]
        if node.args.kwarg:
            node.args.kwarg.arg = new_syms[node.args.kwarg.arg]
        return self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        return self.visit_FunctionDef(node)

    def visit_ClassDef(self, node):
        new_syms = self._new_syms
        if node.name in new_syms:
            node.name = new_syms[node.name]
        return self.generic_visit(node)

    def visit_Lambda(self, node):
        new_syms = self._new_syms
        for arg in node.args.args:
            arg.arg = new_syms[arg.arg]
        return self.generic_visit(node)

    def visit_Global(self, node):
        return self.visit_Nonlocal(node)

    def visit_Nonlocal(self, node):
        new_syms = self._new_syms
        for idx, name in enumerate(node.names):
            node.names[idx] = new_syms[name]
        return self.generic_visit(node)


class RenameVariables(ASTPass):
    def apply(self, curr_ast):
        # need external symbols to be kept the same.
        banned = self._cfg.get('banned', [])
        fis = FindImportedSymbols()
        fis.visit(curr_ast)
        modules = fis.symbols()
        banned += modules

        fs = FindSymbols()
        fs.visit(curr_ast)
        new_syms = fs.counts()

        for sym in new_syms.keys():
            if sym[:2] == '__' and sym[-2:] == '__':
                banned.append(sym)

        for ban in banned:
            if ban in new_syms:
                del new_syms[ban]

        new_syms = map_symbols_to_new_names(new_syms)

        # Apply the modifications to normal uses
        new_ast = UpdateSymbols(new_syms, modules).visit(curr_ast)
        # Update class names
        return new_ast
