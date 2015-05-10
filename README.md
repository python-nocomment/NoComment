NoComment
=========

NoComment is a program that parses Python code and prints a set
of possible types for each parameter of a function. This is to
help aid the process of re-documenting unmaintained code.

To run the program, specify a Python file through standard input:

`python nocomment.py target_file.py`

Note: Please DO NOT write undocumented code with the assumption that
this program can take care of the rest. NoComment is imperfect and is
only meant to alleviate the difficulty of debugging previously unmaintained code.