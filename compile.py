#!/usr/bin/env python

import sys
import compiler

with open(sys.argv[1], 'r') as f:
    ast = compiler.run_parse(f.read())
    if ast is None:
        print("Cannot parse!")
    else:
        try:
            compiler.run_semant(ast)
        except compiler.SemantError as e:
            print("Semantic Analyzer failure: %s" % str(e))
        else:
            print("Success!")
