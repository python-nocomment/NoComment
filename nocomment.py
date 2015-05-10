#!/usr/bin/env python 

import imp
import inspect
import itertools
import os
import re
import StringIO
import sys
import types

def analyze(filepath, verbose=True):
    """Analyzes the module-level methods in a Python source file and recommends documentation
    for methods, which are printed to standard output.

    filepath - A string indicating the location of the file to analyze.
    verbose - A boolean indicating whether to print the step-by-step processes of the analysis.
    """
    mod = imp.load_source('mod', filepath)
    functions = get_functions(mod)

    if verbose:
        print "Checking functions for missing docstrings..."
        for f in functions:
            print (" [missing]   " if f.__doc__ is None else "             ") + f.__name__

    recommendations = {}
    for function in functions:
        recommendations[function] = generate_recommendation(function)

    for (f, r) in recommendations.items():
        print "-"*80
        print f
        print
        print r
    print "-"*80


def get_functions(mod):
    """Extracts all module-level functions from a given module and
    returns them in a list.

    mod - A module.
    """
    functions = []
    for (name, method) in inspect.getmembers(mod, inspect.isfunction):
        functions.append(method)
    return functions

def generate_recommendation(function):
    """Returns a multi-line string describing some recommended specifications
    for the given function.

    function - A function.
    """
    body = ""
    lines = remove_comments(inspect.getsourcelines(function)[0])
    var_names = inspect.getargspec(function).args

    infer_types_retval = infer_types(function, lines, var_names)
    if infer_types_retval is None:
        return "Cannot determine typing."
    else:
        tp, returnarg = infer_types_retval

    zd_data = find_zero_denominators(lines, var_names)
    zd = {v: (v in zd_data) for v in var_names}

    for v in var_names:
        div = " (divisor)" if zd[v] else ""
        buf = ""
        for type_, metric in tp[v]:
            buf += stringify_type(type_) + ", "
        body += (v + div + ": " + buf + "\n")

    # write the likely types for the return argument
    body += "\nReturn type: "
    for type_, metric in returnarg:
        body += stringify_type(type_) + ", "

    return body

supported_types = [types.BooleanType, types.IntType, types.FloatType,
                   types.StringType, types.TupleType, types.ListType,
                   types.DictType, types.NoneType]

def stringify_type(t):
    """Returns a simple string name of a type t. Returns None if type not supported."""
    table = {
        types.BooleanType   : "bool"
    ,   types.IntType       : "int"
    ,   types.FloatType     : "float"
    ,   types.StringType    : "string"
    ,   types.TupleType     : "tuple"
    ,   types.ListType      : "list"
    ,   types.DictType      : "dict"
    ,   types.NoneType      : "None"
    }
    if t in table: return table[t]
    else: return None

def remove_comments(lines):
    """Returns a list of Python source lines with comments removed.

    lines - A list of strings representing lines in part of a Python source file.
    """

    # remove multi-line comments
    single = "\n".join(map(lambda x: x[:-1], lines))
    single = re.sub("'''(.|\n)*'''", "", single)
    single = re.sub('"""(.|\n)*"""', '', single)

    lines = single.split("\n")
    return map(lambda x: x.split("#")[0], lines)

def find_zero_denominators(lines, var_names):
    """Returns a subset of variables in var_names that are used as denominators
    in the list of Python source lines.

    lines - A list of strings representing lines in part of a Python source file.
    var_names - A list of strings representing the variable names used in the parameters.
    """
    output = []
    for line in lines:
        for var in var_names:
            if re.search("/( )*"+var, line):
                output.append(var)
    return list(set(output)) # remove duplicates

def prune(lines_, var_types_):
    """Given the source code of a function and a dictionary mapping parameter names to
    dictionaries mapping types to numerical metrics, prunes the dictionary and returns
    one with unlikely types removed from the dictionary corresponding to each variable
    name.

    lines_ - A list of strings representing lines in part of a Python source file.
    var_types_ - A dictionary mapping strings of variable names to a dictionary mapping
                 types to a numeric score indicating likelihood of the variable's type.
    """
    var_types = var_types_.copy()
    reassigned = {v: False for v in var_types} # to keep track of reassignments
    lines_t = []; lines = []
    for l in lines_[1:]:
        lines_t.append(str(re.sub("'(.)*'", "_", l)))
    for l in lines_t:
        lines.append(str(re.sub('"(.)*"', "_", l)))
    int_methods = [ "bit_length" ]
    float_methods = [ "as_integer_ratio", "is_integer", "hex", "fromhex" ]
    string_methods = [  "capitalize", "center", "count", "decode", "encode", "endswith",
                        "expandtabs", "find", "format", "index", "isalnum", "isdigit",
                        "islower", "isspace", "istitle", "isupper", "join", "ljust",
                        "lower", "lstrip", "partition", "replace", "rfind", "rindex",
                        "rjust", "rpartition", "rsplit", "split", "splitlines",
                        "startswith", "strip", "swapcase", "title", "translate",
                        "upper", "zfill" ]
    dict_methods = [ "clear", "copy", "fromkeys", "get", "has_key", "items", "iteritems",
                     "iterkeys", "itervalues", "keys", "popitem", "setdefault", "update",
                     "values", "viewitems", "viewvalues" ]

    for var in var_types:
        for line in lines:
            # check for any reassignment, stop analysis for now if found
            if re.search("( )+"+var+"( )*=", line) or re.match(var+"( )*=", line):
                reassigned[var] = True
            if not reassigned[var]:
                # prune __getitem__ accessor, a.k.a []
                if re.search(var+"( )*\[", line):
                    if types.BooleanType in var_types[var]: del var_types[var][types.BooleanType]
                    if types.IntType in var_types[var]: del var_types[var][types.IntType]
                    if types.FloatType in var_types[var]: del var_types[var][types.FloatType]
                    if types.NoneType in var_types[var]: del var_types[var][types.NoneType]
                if re.search(var+"( )*\[( )*_\]", line):
                    if types.StringType in var_types[var]: del var_types[var][types.StringType]
                    if types.TupleType in var_types[var]: del var_types[var][types.TupleType]
                    if types.ListType in var_types[var]: del var_types[var][types.ListType]
                # prune __call__ operator, a.k.a ()
                if re.search(var+"( )*\(", line):
                    if types.BooleanType in var_types[var]: del var_types[var][types.BooleanType]
                    if types.IntType in var_types[var]: del var_types[var][types.IntType]
                    if types.FloatType in var_types[var]: del var_types[var][types.FloatType]
                    if types.StringType in var_types[var]: del var_types[var][types.StringType]
                    if types.TupleType in var_types[var]: del var_types[var][types.TupleType]
                    if types.ListType in var_types[var]: del var_types[var][types.ListType]
                    if types.DictType in var_types[var]: del var_types[var][types.DictType]
                    if types.NoneType in var_types[var]: del var_types[var][types.NoneType]
                # prune operators for each type
                if re.search(var+"( )*(\+|\*)", line) or \
                   re.search(        "(\+|\*)( )*"+var+"[^\[\(]", line):
                    if types.NoneType in var_types[var]: del var_types[var][types.NoneType]
                    if types.DictType in var_types[var]: del var_types[var][types.DictType]
                if re.search(var+"( )*(\-|\/|\*\*)", line) or \
                   re.search(        "(\-|\/|\*\*)( )*"+var+"[^\[\(]", line):
                    if types.StringType in var_types[var]: del var_types[var][types.StringType]
                    if types.TupleType in var_types[var]: del var_types[var][types.TupleType]
                    if types.ListType in var_types[var]: del var_types[var][types.ListType]
                    if types.DictType in var_types[var]: del var_types[var][types.DictType]
                if re.search(var+"( )*(\^|%|&|\||<<|>>)", line) or \
                   re.search(        "(\^|%|&|\||<<|>>)( )*"+var+"[^\[\(]", line):
                    if types.StringType in var_types[var]: del var_types[var][types.StringType]
                    if types.TupleType in var_types[var]: del var_types[var][types.TupleType]
                    if types.ListType in var_types[var]: del var_types[var][types.ListType]
                    if types.DictType in var_types[var]: del var_types[var][types.DictType]
                    if types.FloatType in var_types[var]: del var_types[var][types.FloatType]
                    if types.NoneType in var_types[var]: del var_types[var][types.NoneType]
                # check sequence operators
                if re.search("in( )*"+var, line):
                    if types.BooleanType in var_types[var]: del var_types[var][types.BooleanType]
                    if types.IntType in var_types[var]: del var_types[var][types.IntType]
                    if types.FloatType in var_types[var]: del var_types[var][types.FloatType]
                    if types.NoneType in var_types[var]: del var_types[var][types.NoneType]
                if re.search("(len|min|max|list|next|enumerate|sorted|all|any|set|sum|tuple|zip)( )*\(( )*"+var, line):
                    if types.BooleanType in var_types[var]: del var_types[var][types.BooleanType]
                    if types.IntType in var_types[var]: del var_types[var][types.IntType]
                    if types.FloatType in var_types[var]: del var_types[var][types.FloatType]
                    if types.NoneType in var_types[var]: del var_types[var][types.NoneType]
                if re.search(var+"( )*.( )*(append|extend|count|index|insert|pop|remove|reverse|sort)", line):
                    if types.BooleanType in var_types[var]: del var_types[var][types.BooleanType]
                    if types.IntType in var_types[var]: del var_types[var][types.IntType]
                    if types.FloatType in var_types[var]: del var_types[var][types.FloatType]
                    if types.NoneType in var_types[var]: del var_types[var][types.NoneType]
                # look for string methods
                for methodname in string_methods:
                    if re.search(var+"( )*.( )*"+methodname, line):
                        if types.StringType in var_types[var]:
                            var_types[var] = {types.StringType : var_types[var][types.StringType]}
                for methodname in int_methods:
                    if re.search(var+"( )*.( )*"+methodname, line):
                        if types.IntType in var_types[var]:
                            var_types[var] = {types.IntType : var_types[var][types.IntType]}
                for methodname in float_methods:
                    if re.search(var+"( )*.( )*"+methodname, line):
                        if types.FloatType in var_types[var]:
                            var_types[var] = {types.FloatType : var_types[var][types.FloatType]}
                for methodname in dict_methods:
                    if re.search(var+"( )*.( )*"+methodname, line):
                        if types.DictType in var_types[var]:
                            var_types[var] = {types.DictType : var_types[var][types.DictType]}

    return var_types

def infer_types(func, lines, var_names, assumed={}):
    """Tries to infer a type based on its associated operations given a set of
    assumed types for other parameters.

    Returns a tuple where the first element is a dictionary mapping variable string names
    to a list possible types (ranked by most likely first) and
    the second element is a list of likely return types.

    Returns None if a variable loses all possible types, i.e. unknown or unsupported type.
    
    func - A function.
    lines - A list of strings representing lines in part of a Python source file.
    var_names - A list of strings representing the variable names used in the parameters.
    assumed - A dictionary mapping strings corresponding to variable names to the type
              that it should run with (this method will supply a set of values for each type).
    """

    # maps strings of variable names to dictionary mapping types to a numeric score
    # indicating likelihood of the variable's type
    # e.g. variable name { 'a' : { types.BooleanType: 4, types.StringType: 2 } }
    var_types = {v: {t: 0 for t in supported_types} for v in var_names}
    return_types = {t: 0 for t in supported_types}

    # prune unlikely types from each variable's possible set based on scanning
    # the raw source code
    var_types = prune(lines, var_types)


    ## CHECK PRUNE RESULTS TO ENSURE EACH VARIABLE STILL HAS POSSIBLE TYPES
    ## OTHERWISE, SAMPLE_TYPE WILL FAIL
    for var in var_types:
        if len(var_types[var]) == 0:
            return None

    # now run through the function using sample values from each type
    # keep track of return values as well
    perms = sample_type_values(var_names, var_types)
    # prevent printing to stdout and stderr during test runs
    stdout = sys.stdout
    stderr = sys.stderr
    sys.stdout = StringIO.StringIO()
    sys.stderr = StringIO.StringIO()
    for p in perms:
        try:
            retval = func(*p)
            for ndx in range(len(var_names)):
                var_types[var_names[ndx]][type(p[ndx])] += 1
            if type(retval) in return_types:
                return_types[type(retval)] += 1
        except BaseException as e:
            pass
    # restore print functionality
    sys.stdout = stdout
    sys.stderr = stderr

    # only take top 5 type suggestions
    return ({v: sorted(filter(lambda x: x[1] > 0, var_types[v].items()), key=lambda x: -x[1])[:5] \
            for v in var_names}, \
            sorted(filter(lambda x: x[1] > 0, return_types.items()), key=lambda x: -x[1])[:5])

def sample_type_values(var_names, var_types):
    """Provides all permutations of values that should be assigned to each variable in the
    list. Each type that can be assigned to a variable may take on multiple values.
    Returns an itertools object of tuples (whose values are those that should be assigned
    to the variables specified in var_names, in respective order).

    Each variable in var_types must have at least one possible type.

    var_names - A list of strings representing the variable names used in the parameters.
    var_types - A dictionary mapping strings of variable names to a dictionary mapping
                 types to a numeric score indicating likelihood of the variable's type.
    """
    table = {
        types.BooleanType   : [True, False, True, False, True]
    ,   types.IntType       : [-100, 1, 0, 1, 100]
    ,   types.FloatType     : [-1.1, -0.73, 0.0, 0.34, 2.999]
    ,   types.StringType    : ["", "\n", " ", "Hello", "H3llo\n W0rld!"]
    ,   types.TupleType     : [(), (0,1), (2,"zz", False), ("a","b","c"), ([1,2,3], 4)]
    ,   types.ListType      : [ [], [-1.1, "zzz"], [[], [[0]], [0,1]], ["a","b","c"], [1,2,3] ]
    ,   types.DictType      : [{}, {"a": 3}, {1:{1,2}, 4:3}, {0:"h"}, {"b":"c"}]
    ,   types.NoneType      : [None, None, None, None, None]
    }

    # set up possible values across all types for each variable
    values = var_names[:]
    for ndx in range(len(var_names)):
        buf = []
        for t in var_types[var_names[ndx]]:
            for v in table[t]:
                buf.append(v)
        values[ndx] = buf

    return itertools.product(*values)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "Please supply exactly one target file name."
    elif not os.path.isfile(sys.argv[1]):
        print "Specified input is not a file."
    else:
        analyze(sys.argv[1])














