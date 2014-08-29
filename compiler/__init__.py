from .parser import parser
from . import semant

run_parse = parser.parse
run_semant = semant.semant

SemantError = semant.SemantError
