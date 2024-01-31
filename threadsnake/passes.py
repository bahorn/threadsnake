"""
Passes we run over the AST
"""
import copy
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
        Expr, \
        walk, \
        alias, \
        unparse, \
        parse, \
        dump
from _ast import Attribute, Call, BinOp
import re
from remapnames import SymbolMapper


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

            if not isinstance(node.body[0], Expr):
                continue

            if not isinstance(node.body[0].value, Constant):
                continue

            if not isinstance(node.body[0].value.value, str):
                continue

            before = []

            if not isinstance(node, Module):
                before += [Pass()] if len(node.body) == 1 else []
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
    """
    Dict counter.
    """
    if v not in d:
        d[v] = 0
    d[v] += 1


class FindImportedSymbols(NodeVisitor):
    """
    Finds import statements and records the modules used.
    """

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
    """
    Searches the AST for symbols we need to update.
    """

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
        name = unparse(node).split('.')[0]
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
            arg.arg = new_syms.get(arg.arg, arg.arg)
        for arg in node.args.kwonlyargs:
            arg.arg = new_syms.get(arg.arg, arg.arg)
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

    def visit_Call(self, node):
        return self.generic_visit(node)


class SymbolFilter:
    """
    Filter out symbols we don't want to rename.
    """

    def __init__(self, banned_str, banned_regex=[]):
        self._banned_str = banned_str
        self._banned_regex = list(map(re.compile, banned_regex))

    def is_banned(self, symbol_name):
        if symbol_name in self._banned_str:
            return True
        # check against regex
        for regex in self._banned_regex:
            if regex.fullmatch(symbol_name):
                return True
        return False

    def filter(self, symbols):
        res = {}
        for symbol, count in symbols.items():
            if not self.is_banned(symbol):
                res[symbol] = count
        return res


# Function we add into the code.
ATTRIBUTE_LOOK_STR = """
def attribute_lookup(cls, symbol):
    syms = getattr(symbol, 'split')('.', 1)
    rest = [''] if len(syms) == 1 else syms[1]
    r = getattr(cls, syms[0] if hasattr(cls, syms[0]) else remap[syms[0]])
    return r if len(rest) == 1 else attribute_lookup(r, rest)

def attribute_set(cls, symbol, value):
    curr = getattr(symbol, 'split')('.', 1)[0]
    setattr(cls, curr if hasattr(cls, curr) else remap[curr], value)
"""


class InsertHelpers(ASTPass):
    """
    Add in functions to use as helpers.
    """

    to_add = [ATTRIBUTE_LOOK_STR]

    def apply(self, curr_ast):
        new_ast = copy.deepcopy(curr_ast)
        to_add = list(map(parse, self.to_add))
        res = []
        for module in to_add:
            res += module.body
        new_ast.body = res + new_ast.body
        return new_ast


class WrapAttributes(NodeTransformer):
    """
    Wrapping the attribute access with the `attribute_lookup` function.
    """

    def __init__(self, name, banned):
        self._attribute_get, self._attribute_set = name
        self._banned = banned

    def visit_Assign(self, node):
        # we need to split out calls in the targets
        found_attr = False
        for target in node.targets:
            if isinstance(target, Attribute):
                found_attr = True

        if not found_attr:
            return self.generic_visit(node)

        values = [self.visit(node.value)]
        res = []

        for target in node.targets:
            base = node.targets[0]
            res.append(Expr(Call(
                func=Name(self._attribute_set),
                args=(
                    self.visit(base.value),
                    Constant(base.attr),
                    values[0]
                ),
                keywords={}
            )))

        return res

    def visit_AugAssign(self, node):
        # we need to split out calls in the targets
        found_attr = False
        if isinstance(node.target, Attribute):
            found_attr = True

        if not found_attr:
            return self.generic_visit(node)

        value = node.value
        base = node.target
        left_value = self.visit(base)
        new_value = BinOp(op=node.op, left=left_value, right=value)
        return Expr(Call(
            func=Name(self._attribute_set),
            args=(
                self.visit(base.value),
                Constant(base.attr),
                new_value
            ),
            keywords={}
        ))

    def visit_Attribute(self, node):
        # we are trying to merge attributes together
        curr = node.value
        attr = [node.attr]
        if node.attr in self._banned:
            return self.generic_visit(node)
        while isinstance(curr, Attribute):
            attr.append(curr.attr)
            curr = curr.value
        return Call(
            func=Name(self._attribute_get),
            args=(
                self.visit(curr),
                Constant('.'.join(attr[::-1]))
            ),
            keywords={}
        )


class RenameVariables(ASTPass):
    def apply(self, curr_ast):
        sm = SymbolMapper()

        fis = FindImportedSymbols()
        fis.visit(curr_ast)
        modules = fis.symbols()
        sm.add_to_keywords(fis.symbols())

        fs = FindSymbols()
        fs.visit(curr_ast)
        new_syms = fs.counts()

        # need external symbols to be kept the same.
        banned_str = self._cfg.get('banned_str', [])
        banned_str += modules
        banned_regex = self._cfg.get('banned_regex', [])
        # catch things like __name__
        banned_regex.append('^__[a-zA-Z0-9]+__$')

        sf = SymbolFilter(banned_str, banned_regex=banned_regex)
        new_syms = sf.filter(new_syms)
        new_syms = sm.map_symbols(new_syms)

        # filter new_syms done so we don't bother replacing symbols that get
        # used once, or have no need to go through the attribute_lookup
        # function

        dont_care = ['attribute_lookup', 'attribute_set', 'remap']
        new_syms_flip = {
            value: key
            for key, value in filter(
                lambda x: x[0] not in dont_care, new_syms.items()
            )
        }

        # define remap. will already be in the list of symbols, so the rewrite
        # will catch this
        curr_ast.body = [parse(f'remap = {new_syms_flip}')] + curr_ast.body

        # Update symbol names
        new_ast = UpdateSymbols(new_syms, modules).visit(curr_ast)

        # Now replace attribute accesses with calls to `attribute_lookup()`
        new_ast = WrapAttributes(
            (new_syms['attribute_lookup'], new_syms['attribute_set']),
            banned_str
        ).visit(new_ast)

        return new_ast
