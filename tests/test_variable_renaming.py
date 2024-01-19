import unittest
import ast
from passes import RenameVariables


equal_res_cases = [
'''
def func():
    return 42
res = func()
''',
'''
class Magic():
    def __init__(self, blah):
        self._blah = blah
    def mul(self):
        return self._blah ** 2

working = Magic(5)
res = working.mul()
working._blah -= 3
res += working.mul()
'''
]


def run_instance(tree):
    namespace = {'res': None}
    exec(ast.unparse(tree), namespace)
    return namespace['res']


class TestRenameVariables(unittest.TestCase):
    def test_equal_res(self):
        """
        Run the programs before and after renaming, assert they give the same
        output.
        """
        instance = RenameVariables({'banned': ['res']})
        for case in equal_res_cases:
            tree = ast.parse(case)
            res1 = run_instance(tree)
            modified = instance.apply(tree)
            res2 = run_instance(modified)
            self.assertNotEqual(res1, None)
            self.assertNotEqual(res2, None)
            self.assertEqual(res1, res2)
