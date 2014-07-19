import ply.yacc as yacc

# Get the token map from the lexer.  This is required.
from lexer import tokens

#tokens = (
#   'COMMENTINLINE', 'DARROW', 'CLASS', 'IN', 'INHERITS', 'ISVOID', 'LET',
#   'NEW', 'OF', 'NOT', 'LOOP', 'POOL', 'CASE', 'ESAC', 'IF', 'THEN', 'ELSE',
#   'FI', 'WHILE', 'ASSIGN', 'LE', 'PLUS', 'MINUS', 'MULT', 'DIV', 'LPAREN',
#   'RPAREN', 'LBRACE', 'RBRACE', 'DOT', 'COLON', 'COMMA', 'SEMI', 'EQ',
#   'NEG', 'LT', 'AT', 'TYPEID', 'OBJECTID', 'INT_CONST', 'STR_CONST', 'COMMENT'
#)

def p_class(p):
    """class : CLASS TYPEID LBRACE feature_list RBRACE SEMI"""
    p[0] = ('class', p[2], "Object", p[4])

def p_class_inherits(p):
    """class : CLASS TYPEID INHERITS TYPEID LBRACE feature_list RBRACE SEMI"""
    p[0] = ('class', p[2], p[4], p[6])

def p_feature_list_many(p):
    """feature_list : feature_list feature SEMI"""
    p[0] = p[1] + [p[2]]

def p_feature_list_single(p):
    """feature_list : feature SEMI"""
    p[0] = [p[1]]

def p_feature_list_empty(p):
    """feature_list : """
    p[0] = []

def p_feature_method(p):
    """feature : OBJECTID LPAREN formal_list RPAREN COLON TYPEID LBRACE RBRACE"""
    p[0] = ('method', p[1], p[3], p[6], )

def p_feature_method_no_formals(p):
    """feature : OBJECTID LPAREN RPAREN COLON TYPEID LBRACE RBRACE"""
    p[0] = ('method', p[1], [], p[5], )

def p_feature_attr_initialized(p):
    """feature : OBJECTID COLON TYPEID ASSIGN """
    p[0] = ('attr', p[1], p[3], )

def p_feature_attr(p):
    """feature : OBJECTID COLON TYPEID"""
    p[0] = ('attr', p[1], p[3], ('expression', None))

def p_formal_list_many(p):
    """formal_list : formal_list COMMA formal"""
    p[0] = p[1] + [p[3]]

def p_formal_list_single(p):
    """formal_list : formal"""
    p[0] = [p[1]]

def p_formal(p):
    """formal : OBJECTID COLON TYPEID"""
    p[0] = ('formal', p[1], p[3])

# Error rule for syntax errors
def p_error(p):
    print("Syntax error in input!")

# Build the parser
parser = yacc.yacc()

while True:
   try:
       s = input('coolp> ')
   except EOFError:
       break
   if not s: continue
   result = parser.parse(s)
   print(result)
