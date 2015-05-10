# Runs the tests for nocomment.py on the Python source file test-target.py

import unittest
import imp
import sys
import StringIO
import nocomment
import types

class NoCommentTests(unittest.TestCase):
    """Performs tests on all module-level methods in nocomment.py"""

    def test_analyze(self):
        """Verifies that the function runs successfully. Random ordering of variables
        and types makes this nondeterministic. Printing to stdout is suppressed."""
        stdout = sys.stdout
        temp_output = StringIO.StringIO()
        sys.stdout = temp_output
        nocomment.analyze('./test-target.py')
        assert(len(temp_output.getvalue()) > 0)
        sys.stdout = stdout

    def test_get_functions(self):
        """Verifies the right number of module-level functions in the target source file."""
        mod = imp.load_source('mod', './test-target.py')
        self.assertEqual(5, len(nocomment.get_functions(mod)))

    def test_generate_recommendation(self):
        """Verifies that the function runs successfully. Random ordering of variables
        and types make this nondeterministic."""
        def foo(a, b, c, d):
            print b, c #, d
            a = d/a
            return a*b + c*d
        nocomment.generate_recommendation(foo)

    def test_stringify_type(self):
        """Verifies that the program's supported types have matching string descriptors."""
        self.assertEqual("bool"  , nocomment.stringify_type(types.BooleanType))
        self.assertEqual("int"   , nocomment.stringify_type(types.IntType))
        self.assertEqual("float" , nocomment.stringify_type(types.FloatType))
        self.assertEqual("string", nocomment.stringify_type(types.StringType))
        self.assertEqual("tuple" , nocomment.stringify_type(types.TupleType))
        self.assertEqual("list"  , nocomment.stringify_type(types.ListType))
        self.assertEqual("dict"  , nocomment.stringify_type(types.DictType))
        self.assertEqual("None"  , nocomment.stringify_type(types.NoneType))
        self.assertEqual(None    , nocomment.stringify_type(types.LongType))

    def test_remove_comments(self):
        """Verifies that Python comments are removed from source text."""
        lines = ['def func_with_comments(a, b):\n',
                 '    c = 5/b\n', '    d = a/5\n',
                 '    # test comment for removal\n',
                 '    print a\n',
                 "    '''\n",
                 '    test single quote multi-line comments\n',
                 "    '''\n",
                 '    """ test single quote inside double quote multi-line comments \'\'\' ayy \'\'\' """\n',
                 '    """ test comment for removal\n',
                 '    """\n',
                 '    return a/b # test comment for removal\n']
        expected = ['def func_with_comments(a, b):',
                    '    c = 5/b',
                    '    d = a/5',
                    '    ',
                    '    print a',
                    '     ',
                    '    return a/b ']
        self.assertEqual(expected, nocomment.remove_comments(lines))

    def test_find_zero_denominators(self):
        """Verifies that zero denominator variables are found."""
        lines = ['def divide(a, b):',
                 "    '''existing docstring'''",
                 '    return a/b']
        expected = ['b']
        self.assertEqual(set(expected), set(nocomment.find_zero_denominators(lines, ['a', 'b'])))

    def test_prune(self):
        """Verifies that a variable's set of possible types are pruned of impossible
        ones based on source code analysis."""
        all_types = {types.BooleanType: 0, types.IntType: 0, types.FloatType: 0,
                    types.StringType: 0, types.TupleType: 0, types.ListType: 0,
                    types.DictType: 0, types.NoneType: 0}
        var_types = {"a": all_types.copy(), "b": all_types.copy(), "c": all_types.copy()}
        lines = ['def foo(a, b, c):',
                 '    d = a * b,',
                 '    d = a + b',
                 '    d = b - a',
                 '    a = d/a',
                 '    return a*b + c[0]*d']
        expected = {"a": {types.BooleanType: 0, types.IntType: 0, types.FloatType: 0,
                          types.StringType: 0, types.TupleType: 0, types.ListType: 0,
                         },
                    "b": {types.BooleanType: 0, types.IntType: 0, types.FloatType: 0},
                    "c": {types.StringType: 0, types.TupleType: 0, types.ListType: 0,
                          types.DictType: 0}
                   }
        self.assertEqual(expected, nocomment.prune(lines, var_types))

    def test_prune_2(self):
        """Verifies that the pruning process does not progress past reassignments."""
        var_types = {"a": {types.BooleanType: 0, types.DictType: 0, types.ListType: 0}}
        lines = ['def foo(a):',
                 '    b = a[0]',
                 '    c = a*3',
                 '    a = e',
                 '    d = a - 4']
        expected = {"a": {types.ListType: 0}}
        self.assertEqual(expected, nocomment.prune(lines, var_types))

    def test_infer_types(self):
        """Verifies that the function runs successfully. Random ordering of variables
        and types make this nondeterministic."""
        def foo(a, b, c, d):
            print b, c #, d
            a = d/a
            return a*b + c*d
        lines = ['def foo(a, b, c, d):',
                 '    print b, c #, d',
                 '    a = d/a',
                 '    return a*b + c*d']
        nocomment.infer_types(foo, lines, ['a', 'b', 'c', 'd'])

    def test_sample_type_values(self):
        """Verifies that all permutations of sample type values are provided."""
        p = nocomment.sample_type_values(['a', 'b', 'c'],
                                         {
                                             'a' : {types.BooleanType: 1},
                                             'b' : {types.IntType: 0,
                                                    types.FloatType: 2},
                                             'c' : {types.FloatType: 3}
                                         })
        expected = [(True, -100, -1.1), (True, -100, -0.73), (True, -100, 0.0),
                    (True, -100, 0.34), (True, -100, 2.999), (True, 1, -1.1),
                    (True, 1, -0.73), (True, 1, 0.0), (True, 1, 0.34), (True, 1, 2.999),
                    (True, 0, -1.1), (True, 0, -0.73), (True, 0, 0.0), (True, 0, 0.34),
                    (True, 0, 2.999), (True, 1, -1.1), (True, 1, -0.73), (True, 1, 0.0),
                    (True, 1, 0.34), (True, 1, 2.999), (True, 100, -1.1), (True, 100, -0.73),
                    (True, 100, 0.0), (True, 100, 0.34), (True, 100, 2.999), (True, -1.1, -1.1),
                    (True, -1.1, -0.73), (True, -1.1, 0.0), (True, -1.1, 0.34),
                    (True, -1.1, 2.999), (True, -0.73, -1.1), (True, -0.73, -0.73),
                    (True, -0.73, 0.0), (True, -0.73, 0.34), (True, -0.73, 2.999), (True, 0.0, -1.1),
                    (True, 0.0, -0.73), (True, 0.0, 0.0), (True, 0.0, 0.34), (True, 0.0, 2.999),
                    (True, 0.34, -1.1), (True, 0.34, -0.73), (True, 0.34, 0.0), (True, 0.34, 0.34),
                    (True, 0.34, 2.999), (True, 2.999, -1.1), (True, 2.999, -0.73),
                    (True, 2.999, 0.0), (True, 2.999, 0.34), (True, 2.999, 2.999),
                    (False, -100, -1.1), (False, -100, -0.73), (False, -100, 0.0),
                    (False, -100, 0.34), (False, -100, 2.999), (False, 1, -1.1),
                    (False, 1, -0.73), (False, 1, 0.0), (False, 1, 0.34), (False, 1, 2.999),
                    (False, 0, -1.1), (False, 0, -0.73), (False, 0, 0.0), (False, 0, 0.34),
                    (False, 0, 2.999), (False, 1, -1.1), (False, 1, -0.73), (False, 1, 0.0),
                    (False, 1, 0.34), (False, 1, 2.999), (False, 100, -1.1), (False, 100, -0.73),
                    (False, 100, 0.0), (False, 100, 0.34), (False, 100, 2.999), (False, -1.1, -1.1),
                    (False, -1.1, -0.73), (False, -1.1, 0.0), (False, -1.1, 0.34),
                    (False, -1.1, 2.999), (False, -0.73, -1.1), (False, -0.73, -0.73),
                    (False, -0.73, 0.0), (False, -0.73, 0.34), (False, -0.73, 2.999),
                    (False, 0.0, -1.1), (False, 0.0, -0.73), (False, 0.0, 0.0), (False, 0.0, 0.34),
                    (False, 0.0, 2.999), (False, 0.34, -1.1), (False, 0.34, -0.73), (False, 0.34, 0.0),
                    (False, 0.34, 0.34), (False, 0.34, 2.999), (False, 2.999, -1.1), (False, 2.999, -0.73),
                    (False, 2.999, 0.0), (False, 2.999, 0.34), (False, 2.999, 2.999), (True, -100, -1.1),
                    (True, -100, -0.73), (True, -100, 0.0), (True, -100, 0.34), (True, -100, 2.999), 
                    (True, 1, -1.1), (True, 1, -0.73), (True, 1, 0.0), (True, 1, 0.34), (True, 1, 2.999),
                    (True, 0, -1.1), (True, 0, -0.73), (True, 0, 0.0), (True, 0, 0.34), (True, 0, 2.999),
                    (True, 1, -1.1), (True, 1, -0.73), (True, 1, 0.0), (True, 1, 0.34), (True, 1, 2.999),
                    (True, 100, -1.1), (True, 100, -0.73), (True, 100, 0.0), (True, 100, 0.34),
                    (True, 100, 2.999), (True, -1.1, -1.1), (True, -1.1, -0.73), (True, -1.1, 0.0),
                    (True, -1.1, 0.34), (True, -1.1, 2.999), (True, -0.73, -1.1), (True, -0.73, -0.73),
                    (True, -0.73, 0.0), (True, -0.73, 0.34), (True, -0.73, 2.999), (True, 0.0, -1.1),
                    (True, 0.0, -0.73), (True, 0.0, 0.0), (True, 0.0, 0.34), (True, 0.0, 2.999),
                    (True, 0.34, -1.1), (True, 0.34, -0.73), (True, 0.34, 0.0), (True, 0.34, 0.34),
                    (True, 0.34, 2.999), (True, 2.999, -1.1), (True, 2.999, -0.73), (True, 2.999, 0.0),
                    (True, 2.999, 0.34), (True, 2.999, 2.999), (False, -100, -1.1), (False, -100, -0.73),
                    (False, -100, 0.0), (False, -100, 0.34), (False, -100, 2.999), (False, 1, -1.1),
                    (False, 1, -0.73), (False, 1, 0.0), (False, 1, 0.34), (False, 1, 2.999),
                    (False, 0, -1.1), (False, 0, -0.73), (False, 0, 0.0), (False, 0, 0.34),
                    (False, 0, 2.999), (False, 1, -1.1), (False, 1, -0.73), (False, 1, 0.0),
                    (False, 1, 0.34), (False, 1, 2.999), (False, 100, -1.1), (False, 100, -0.73),
                    (False, 100, 0.0), (False, 100, 0.34), (False, 100, 2.999), (False, -1.1, -1.1),
                    (False, -1.1, -0.73), (False, -1.1, 0.0), (False, -1.1, 0.34), (False, -1.1, 2.999),
                    (False, -0.73, -1.1), (False, -0.73, -0.73), (False, -0.73, 0.0), (False, -0.73, 0.34),
                    (False, -0.73, 2.999), (False, 0.0, -1.1), (False, 0.0, -0.73), (False, 0.0, 0.0),
                    (False, 0.0, 0.34), (False, 0.0, 2.999), (False, 0.34, -1.1), (False, 0.34, -0.73),
                    (False, 0.34, 0.0), (False, 0.34, 0.34), (False, 0.34, 2.999), (False, 2.999, -1.1),
                    (False, 2.999, -0.73), (False, 2.999, 0.0), (False, 2.999, 0.34), (False, 2.999, 2.999),
                    (True, -100, -1.1), (True, -100, -0.73), (True, -100, 0.0), (True, -100, 0.34),
                    (True, -100, 2.999), (True, 1, -1.1), (True, 1, -0.73), (True, 1, 0.0), (True, 1, 0.34),
                    (True, 1, 2.999), (True, 0, -1.1), (True, 0, -0.73), (True, 0, 0.0), (True, 0, 0.34),
                    (True, 0, 2.999), (True, 1, -1.1), (True, 1, -0.73), (True, 1, 0.0), (True, 1, 0.34),
                    (True, 1, 2.999), (True, 100, -1.1), (True, 100, -0.73), (True, 100, 0.0), (True, 100, 0.34),
                    (True, 100, 2.999), (True, -1.1, -1.1), (True, -1.1, -0.73), (True, -1.1, 0.0),
                    (True, -1.1, 0.34), (True, -1.1, 2.999), (True, -0.73, -1.1), (True, -0.73, -0.73),
                    (True, -0.73, 0.0), (True, -0.73, 0.34), (True, -0.73, 2.999), (True, 0.0, -1.1),
                    (True, 0.0, -0.73), (True, 0.0, 0.0), (True, 0.0, 0.34), (True, 0.0, 2.999),
                    (True, 0.34, -1.1), (True, 0.34, -0.73), (True, 0.34, 0.0), (True, 0.34, 0.34),
                    (True, 0.34, 2.999), (True, 2.999, -1.1), (True, 2.999, -0.73), (True, 2.999, 0.0),
                    (True, 2.999, 0.34), (True, 2.999, 2.999)]
        self.assertEqual(set(expected), set(p))

if __name__ == '__main__':
    unittest.main()
