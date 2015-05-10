# # This file contains sample source code that should is analyzed by
# # nocomment.py during testing

def hello():
    print "hello world"

def func_with_comments(a, b):
    c = 5/b
    d = a/5
    # test comment for removal
    print a
    '''
    test single quote multi-line comments
    '''
    """ test single quote inside double quote multi-line comments ''' ayy ''' """
    """ test comment for removal
    """
    return a/b # test comment for removal

def divide(a, b):
    '''existing docstring'''
    return a/b

def greeting(name):
    return 'Hello ' + name # from https://www.python.org/dev/peps/pep-0484/

def undeterminable(a,b):
    c = a + b;
    c = a()

