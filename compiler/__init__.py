from .parser import parser
from . import semant
from .codegen import cgen

run_parse = parser.parse
run_semant = semant.semant
run_codegen = cgen

SemantError = semant.SemantError
