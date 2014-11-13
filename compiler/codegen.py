from .parser import Class, Method, Attr, Object, Int, Str, Block, Assign, \
        Dispatch, StaticDispatch, Plus, Sub, Mult, Div, Lt, Le, Eq, \
        If, While, Let, Case, New, Isvoid, Neg, Not, Bool
import io
import functools
import compiler.memorymgr as mm

code = io.StringIO()

gc_functions = {
    'NO_GC': ('_NoGC_Init', '_NoGC_Collect')
}

# support functions
def header(text):
    """write a header section to the code obj"""
    code.write("%s:\n" % text)
def comment(text):
    """write a comment to the code obj"""
    code.write("#%s\n" % text)
def line(text):
    """write a indented line to the code obj"""
    code.write("\t%s\n" % text)
def lines(lines):
    """write many indented line to the code obj"""
    for text in lines:
        code.write("\t%s\n" % text)
# end support


def emit_global_data():
    """emit code for constants and global declarations"""
    line(".data")
    line(".align 2")
    globaldecls = ['class_nameTab', 'Main_protObj', 'Int_protObj', 'String_protObj', 'bool_const0', 'bool_const1', '_int_tag', '_bool_tag', '_string_tag']
    for g in globaldecls:
        line(".globl %s" % g)
    header("_int_tag")
    line(".word 2")
    header("_bool_tag")
    line(".word 3")
    header("_string_tag")
    line(".word 4")

def emit_select_gc(type_of_gc, test_mode=False):
    """emit code that selects the type of garbage collection we want"""
    initializer, collector = gc_functions[type_of_gc]
    line(".globl _MemMgr_INITIALIZER")
    header("_MemMgr_INITIALIZER")
    line(".word %s" % initializer)

    line(".globl _MemMgr_COLLECTOR")
    header("_MemMgr_COLLECTOR")
    line(".word %s" % collector)

    line(".globl _MemMgr_TEST")
    header("_MemMgr_TEST")
    if test_mode:
        line(".word 1")
    else:
        line(".word 0")


def traverse_for_symbols(expression, strhandle, inthandle):
    if any(isinstance(expression, X) for X in [Isvoid, Neg, Not]):
        traverse_for_symbols(expression.body, strhandle, inthandle)
    elif any(isinstance(expression, X) for X in [Eq, Lt, Le, Plus, Sub, Mult, Div]):
        traverse_for_symbols(expression.first, strhandle, inthandle)
        traverse_for_symbols(expression.second, strhandle, inthandle)
    elif isinstance(expression, While):
        traverse_for_symbols(expression.predicate, strhandle, inthandle)
        traverse_for_symbols(expression.body, strhandle, inthandle)
    elif isinstance(expression, Let):
        traverse_for_symbols(expression.init, strhandle, inthandle)
        traverse_for_symbols(expression.body, strhandle, inthandle)
    elif isinstance(expression, Block):
        for expr in expression.body:
            traverse_for_symbols(expr, strhandle, inthandle)
    elif isinstance(expression, Assign):
        traverse_for_symbols(expression.body, strhandle, inthandle)
        traverse_for_symbols(expression.name, strhandle, inthandle)
    elif isinstance(expression, Dispatch) or isinstance(expression, StaticDispatch):
        traverse_for_symbols(expression.body, strhandle, inthandle)
        for expr in expression.expr_list:
            traverse_for_symbols(expr, strhandle, inthandle)
    elif isinstance(expression, If):
        traverse_for_symbols(expression.predicate, strhandle, inthandle)
        traverse_for_symbols(expression.then_body, strhandle, inthandle)
        traverse_for_symbols(expression.else_body, strhandle, inthandle)
    elif isinstance(expression, Case):
        traverse_for_symbols(expression.expr, strhandle, inthandle)
        for case in expression.case_list:
            traverse_for_symbols(case[2], strhandle, inthandle)
    elif isinstance(expression, Int):
        inthandle(expression)
    elif isinstance(expression, Str):
        strhandle(expression)


def build_symbol_tables(ast):
    """builds a table of constants of type string, int and boolean"""
    def handle(to_dict, expr):
        to_dict.update({expr.content: expr})

    strings = {}
    ints = {}

    def strhandle(expr):
        strings.update({expr.content: expr})
        # string lengths are part of the constants
        strlen = Int(len(expr.content))
        ints.update({strlen.content: strlen})

    inthandle = functools.partial(handle, ints)

    for cl in ast:
        clname = Str(cl.name)
        strhandle(clname)  # have class names in the string table
        for feature in cl.feature_list:
            traverse_for_symbols(feature.body, strhandle, inthandle)
    return strings, ints


def emit_string_code(s, ints):
    line(".word -1")
    header("str_const%s" % id(s))
    line(".word 4")  # string tag
    line(".word %d" % (
        3 + # default obj fields
        1 + # string slots
       (len(s) + 4) / 4  # obj size
    ))
    line(".word String_dispTab")
    len_obj = ints[len(s.content)]
    line(".word int_const%s" % id(len_obj))
    if len(s.content) > 0:
        line(".ascii \"%s\"" % s.content)
    line(".byte 0")
    line(".align 2")


def emit_int_code(s):
    line(".word -1")
    header("int_const%s" % id(s))
    line(".word 2")  # int tag
    line(".word %d" % (
        3 + # default obj fields
        1 # int slots  FIXME check
    ))
    line(".word Int_dispTab")
    line(".word %d" % s.content)


def emit_bool_code(s):
    line(".word -1")
    header("bool_const%s" % id(s))
    line(".word 3")  # bool tag
    line(".word %d" % (
        3 + # default obj fields
        1 # int slots  FIXME check
    ))
    line(".word Bool_dispTab")
    line(".word %d" % s.content)


def emit_symbol_tables_for_constants(strings, ints, bools):
    """emit constants into the program layout, so they can be reused through-out the program"""
    for s in strings.values():
        emit_string_code(s, ints)
    for s in ints.values():
        emit_int_code(s)
    for s in bools.values():
        emit_bool_code(s)


def emit_class_name_table(classes_dict, strings):
    comment("class name lookup table (index -> classname)")
    for clname, cl in classes_dict.items():
        comment(clname)
        line(".word str_const%s" % id(strings[clname]))

def emit_inheritance_table(classes_dict, classes_list):
    comment("inheritance table (index -> class id) maps to parent id")
    line(".globl InheritanceTable")
    header("InheritanceTable")
    comment("class list: %s" % classes_list)
    for clname, cl in classes_dict.items():
        comment(clname)
        parent = classes_dict.get(cl.parent)
        if parent:
            line(".word %s" % classes_list.index(parent.name))
        else:
            line(".word 0")


def emit_prototype_objects(classes_dict, classes_list):
    comment("PROTOTYPE OBJECTS (memory state at instantiation)")
    for clname, cl in classes_dict.items():
        line(".word -1")  # GC marker
        header("%s_protObj" % clname)
        line(".word %s" % classes_list.index(clname))
        attr_count = len([x for x in cl.feature_list if isinstance(x, Attr)])
        line(".word {}".format(
             3 + # prot obj fixed size
             attr_count
        ))
        line(".word %s_dispTab" % clname)
        for feat in cl.feature_list:
            if isinstance(feat, Attr):
                # print default values for attributes
                if feat.type == "Int":
                    line(".word 0")
                elif feat.type == "Bool":
                    line(".word 0")  # FIXME shall we init with False?
                elif feat.type == "String":
                    line("")


def emit_dispatch_tables(classes_dict):
    comment("DISPATCH TABLES OBJECTS")
    for clname, cl in classes_dict.items():
        header("%s_dispTab" % clname)
        for feat in cl.feature_list:
            if isinstance(feat, Method):
                clname = feat.inherited_from
                if clname is None:
                    clname = cl.name
                line(".word %s.%s" % (clname, feat.name))


def code_global_text(classes_dict):
    line(".globl heap_start")
    header("heap_start")
    line(".word 0")
    line(".text")
    line(".globl Main_init")
    line(".globl Int_init")
    line(".globl String_init")
    line(".globl Bool_init")
    line(".globl Main.main")


def emit_initialization_functions(classes_dict):
    non_argument_frame_bytes = 12
    stack_size = non_argument_frame_bytes
    for clname, cl in classes_dict.items():
        header("%s_init" % clname)
        if cl.parent:
            line("jal %s_init" % cl.parent)
        lines([
            "sw $fp,  0($sp) # store frame pointer in top-most portion of stack",
            "move $fp, $sp",
        ])
        mm.enter_frame()
        line(mm.codestack_push(stack_size))
        lines([
            "sw $ra,  -4($fp)", # store ra and s0
            "sw $s0,  -8($fp)",
        ])
        for feat in cl.feature_list:
            if isinstance(feat, Attr):
                if feat.body is None:
                    comment("no init value for %s" % feat.name)
                else:
                    comment("init-ed value for %s" % feat.name)



def cgen(ast, classes_dict):
    """main function for code generation"""
    comment("start of generated code")
    emit_global_data()
    emit_select_gc("NO_GC")

    strings, ints = build_symbol_tables(ast)
    bools = {False: Bool(False), True: Bool(True)}

    emit_symbol_tables_for_constants(strings, ints, bools)
    emit_class_name_table(classes_dict, strings)

    classes_list = list(classes_dict.keys())  # use this list indexes to refer to classes

    emit_inheritance_table(classes_dict, classes_list)  # FIXME check this
    emit_prototype_objects(classes_dict, classes_list)
    emit_dispatch_tables(classes_dict)

    code_global_text(classes_dict)
    emit_initialization_functions(classes_dict)

    return code


