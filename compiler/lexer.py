import ply.lex as lex

# List of token names.   This is always required
tokens = (
   'COMMENTINLINE', 'DARROW', 'CLASS', 'IN', 'INHERITS', 'ISVOID', 'LET',
   'NEW', 'OF', 'NOT', 'LOOP', 'POOL', 'CASE', 'ESAC', 'IF', 'THEN', 'ELSE',
   'FI', 'WHILE', 'ASSIGN', 'LE', 'PLUS', 'MINUS', 'MULT', 'DIV', 'LPAREN',
   'RPAREN', 'LBRACE', 'RBRACE', 'DOT', 'COLON', 'COMMA', 'SEMI', 'EQ',
   'NEG', 'LT', 'AT', 'TYPEID', 'OBJECTID', 'INT_CONST', 'STR_CONST', 'COMMENT'
)

reserved = ['class', 'in', 'inherits', 'isvoid', 'let', 'new', 'of', 'not', 'loop',
            'pool', 'case', 'esac', 'if', 'then', 'else', 'fi', 'while']

# Regular expression rules for simple tokens
t_ignore_COMMENTINLINE = r'--[^\n]*'
t_DARROW = '=>'
t_ASSIGN = '<-'
t_LE = '<='
t_PLUS = r'\+'
t_MINUS = r'-'
t_MULT = r'\*'
t_DIV = r'/'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBRACE = r'\{'
t_RBRACE = r'\}'
t_DOT = r'\.'
t_COLON = ':'
t_COMMA = ','
t_SEMI = ';'
t_EQ = '='
t_NEG = '~'
t_LT = '<'
t_AT = '@'

def t_objects_types_and_reserved_words(t):
    r'[a-zA-Z][a-zA-Z0-9_]*'
    if t.value.lower() in reserved:
        t.type = t.value.upper()
    else:
        if t.value[0].islower():
            t.type = 'OBJECTID'
        else:
            t.type = 'TYPEID'
    return t

def t_INT_CONST(t):
    r'\d+'
    t.value = int(t.value)
    return t

# Define a rule so we can track line numbers
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

t_ignore  = ' \t\r\f'

# Error handling rule
def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)


# USE STATES FOR COMMENTS AND STRINGS
states = (
  ("STRING", "exclusive"),
  ("COMMENT", "exclusive"),
)

# STRING STATE
def t_start_string(t):
    r"\""
    t.lexer.push_state("STRING")
    t.lexer.string_backslashed = False
    t.lexer.stringbuf = ""

def t_STRING_newline(t):
    r"\n"
    t.lexer.lineno += 1
    if not t.lexer.string_backslashed:
        print("String newline not escaped")
        t.lexer.skip(1)
    else:
        t.lexer.string_backslashed = False

def t_STRING_end(t):
    r"\""
    if not t.lexer.string_backslashed:
        t.lexer.pop_state()
        # TODO: insert checks
        t.value = t.lexer.stringbuf
        t.type = "STR_CONST"
        return t
    else:
        t.lexer.stringbuf += '"'
        t.lexer.string_backslashed = False

def t_STRING_anything(t):
    r"[^\n]"
    if t.lexer.string_backslashed:
        if t.value == 'b':
            t.lexer.stringbuf.append('\b')
        elif t.value == 't':
            t.lexer.stringbuf.append('\t')
        elif t.value == 'n':
            t.lexer.stringbuf.append('\n')
        elif t.value == 'f':
            t.lexer.stringbuf.append('\f')
        elif t.value == '\\':
            t.lexer.stringbuf.append('\\')
        else:
            t.lexer.stringbuf.append(t.value)
        t.lexer.string_backslashed = False
    else:
        if t.value != '\\':
            t.lexer.stringbuf += t.value
        else:
            t.lexer.string_backslashed = True

t_STRING_ignore = ''
def t_STRING_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)


# COMMENT STATE
def t_start_comment(t):
    r"\(\*"
    t.lexer.push_state("COMMENT")
    t.lexer.comment_count = 0

def t_COMMENT_startanother(t):
    r"\(\*"
    t.lexer.comment_count += 1

def t_COMMENT_end(t):
    r"\*\)"
    if t.lexer.comment_count == 0:
        t.lexer.pop_state()
    else:
        t.lexer.comment_count -= 1

t_COMMENT_ignore = ''
def t_COMMENT_error(t):
    t.lexer.skip(1)


# Build the lexer
lexer = lex.lex()

if __name__ == '__main__':
    while 1:
        try:
            s = input('cool> ')   # Use raw_input on Python 2
        except EOFError:
            break
        # Give the lexer some input
        lexer.input(s)

        # Tokenize
        while True:
            tok = lexer.token()
            if not tok: break      # No more input
            print(tok)
