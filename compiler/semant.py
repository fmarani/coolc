from .parser import Class, Method, Attr, Object, Int, Str, Block, Assign, \
        Dispatch, StaticDispatch, SelfDispatch, Plus, Sub, Mult, Div, Lt, Le, Eq, \
        If, While, Let, Case, New, Isvoid, Neg, Not

from collections import defaultdict, MutableMapping
import warnings


class SemantError(Exception):
    pass


class SemantWarning(Warning):
    pass


#classes_dict = {}
#inheritance_graph = defaultdict(set)  # format {'classname': {'childclass1', 'childclass2'}}


def install_base_classes(ast):
    """purpose of this is to add base classes always available in the language"""
    objc = Class("Object", None, [
        Method('cool_abort', [], 'Object', None),  # aborts the program
        Method('type_name', [], 'String', None),  # returns string repr of classname
        Method('copy', [], 'SELF_TYPE', None),  # object copy
    ])
    ioc = Class("IO", "Object", [
        Method('out_string', [('arg', 'String')], 'SELF_TYPE', None),  # outputs a string to stdio
        Method('out_int', [('arg', 'Int')], 'SELF_TYPE', None),  # outputs a int to stdio
        Method('in_string', [], 'String', None),  # inputs a string from stdio
        Method('in_int', [], 'Int', None),  # inputs a string from stdio
    ])
    intc = Class("Int", "Object", [
        Attr('_val', '_prim_slot', None)  # unboxed value, untyped
    ])
    boolc = Class("Bool", "Object", [
        Attr('_val', '_prim_slot', None)  # unboxed value, untyped
    ])
    stringc = Class("String", "Object", [
        Attr('_val', 'Int', None),  # string length
        Attr('_str_field', '_prim_slot', None),  # untyped string
        Method('length', [], 'Int', None),  # returns the string length
        Method('concat', [('arg', 'String')], 'String', None),  # str concatenation
        Method('substr', [('arg1', 'Int'), ('arg2', 'Int')], 'String', None),  # str subselection
    ])
    ast += [objc, ioc, intc, boolc, stringc]


def build_inheritance_graph(ast):
    global classes_dict, inheritance_graph
    classes_dict = {}
    inheritance_graph = defaultdict(set)  # format {'classname': {'childclass1', 'childclass2'}}
    for cl in ast:
        if cl.name in classes_dict:
            raise SemantError("class %s already defined" % cl.name)
        classes_dict[cl.name] = cl
        inheritance_graph[cl.parent].add(cl.name)


def check_for_undefined_classes():
    for parentc in inheritance_graph.keys():
        if parentc not in classes_dict and parentc != "Object":
            warnings.warn("classes %s inherit from an undefined parent %s" % (inheritance_graph[parentc], parentc), SemantWarning)
            inheritance_graph['Object'] |= inheritance_graph[parentc]  # intermediate class does not exist so make these classes inherit from Object
            del inheritance_graph[parentc]


def impede_inheritance_from_base_classes():
    for parent in ['String', 'Int', 'Bool']:
        for cl_name in inheritance_graph[parent]:
            raise SemantError("Class %s cannot inherit from base class %s" % (cl_name, parent))


def visit_inheritance_tree(start_class, visited):
    visited[start_class] = True

    if start_class not in inheritance_graph.keys():
        return True

    for childc in inheritance_graph[start_class]:
        #print("%s to %s" % (start_class, childc))
        visit_inheritance_tree(childc, visited)

    return True

def check_for_inheritance_cycles():
    visited = {}
    for parent_name in inheritance_graph.keys():
        visited[parent_name] = False
        for cl_name in inheritance_graph[parent_name]:
            visited[cl_name] = False
    visit_inheritance_tree("Object", visited)
    for k,v in visited.items():
        if not v:
            raise SemantError("%s involved in an inheritance cycle." % k)


class VariablesScopeDict(MutableMapping):
    """dictionary of varname->type that represent variable scope in the ast"""

    def __init__(self):
        self.store = [dict()]

    def __getitem__(self, key):
        for scope in self.store[::-1]:
            if key in scope:
                return scope[key]
        raise KeyError(key)

    def __setitem__(self, key, value):
        self.store[-1][key] = value

    def __delitem__(self, key):
        del self.store[-1][key]

    def __iter__(self):
        raise NotImplementedError

    def __len__(self):
        raise NotImplementedError

    def new_scope(self):
        self.store.append(dict())

    def destroy_scope(self):
        del self.store[-1]


def check_variable_scopes(cl):
    variable_scopes = VariablesScopeDict()
    # in COOL methods are not in the same variable scope, which means we can
    # have methods with same name as variables
    method_scopes = {}
    attr_seen = set()
    method_seen = set()
    for feature in cl.feature_list:
        if isinstance(feature, Attr):
            if feature.name in attr_seen:
                raise SemantError("attribute %s is already defined" % feature.name)
            attr_seen.add(feature.name)
            variable_scopes[feature.name] = feature.type
            traverse_expression(feature.body, variable_scopes)
        elif isinstance(feature, Method):
            if feature.name in method_seen:
                raise SemantError("method %s is already defined" % feature.name)
            method_seen.add(feature.name)
            method_scopes[feature.name] = {}

            formals_seen = set()
            for formal in feature.formal_list:
                if formal in formals_seen:
                    raise SemantError("formal %s in method %s is already defined" % (formal[0], feature.name))
                formals_seen.add(formal)
                method_scopes[feature.name][formal[0]] = formal[1]
            method_scopes[feature.name]['return'] = feature.return_type

            variable_scopes.new_scope()
            traverse_expression(feature.body, variable_scopes)
            variable_scopes.destroy_scope()


def traverse_expression(expression, variable_scopes):
    if isinstance(expression, Isvoid):
        traverse_expression(expression.body, variable_scopes)
    elif any(isinstance(expression, X) for X in [Eq, Lt, Le]):
        traverse_expression(expression.first, variable_scopes)
        traverse_expression(expression.second, variable_scopes)
    elif isinstance(expression, Neg):
        traverse_expression(expression.body, variable_scopes)
    elif any(isinstance(expression, X) for X in [Plus, Sub, Mult, Div]):
        traverse_expression(expression.first, variable_scopes)
        traverse_expression(expression.second, variable_scopes)
    elif isinstance(expression, While):
        traverse_expression(expression.predicate, variable_scopes)
        traverse_expression(expression.body, variable_scopes)
    elif isinstance(expression, Let):
        # LET creates a new scope
        variable_scopes.new_scope()
        variable_scopes[expression.object] = expression.type
        traverse_expression(expression.init, variable_scopes)
        traverse_expression(expression.body, variable_scopes)
        variable_scopes.destroy_scope()
    elif isinstance(expression, Block):
        for expr in expression.body:
            traverse_expression(expr, variable_scopes)
    elif isinstance(expression, Assign):
        traverse_expression(expression.body, variable_scopes)
    elif isinstance(expression, Dispatch):
        traverse_expression(expression.body, variable_scopes)
        for expr in expression.expr_list:
            traverse_expression(expr, variable_scopes)
    elif isinstance(expression, If):
        traverse_expression(expression.predicate, variable_scopes)
        traverse_expression(expression.then_body, variable_scopes)
        traverse_expression(expression.else_body, variable_scopes)
    elif isinstance(expression, Case):
        traverse_expression(expression.expr, variable_scopes)
        for case in expression.case_list:
            variable_scopes.new_scope()  # every branch of case has its own scope
            variable_scopes[case[0]] = case[1]
            traverse_expression(case[2], variable_scopes)
    elif isinstance(expression, Object):
        if expression.name not in variable_scopes:
            raise SemantError("variable %s not in scope" % expression.name)







def semant(ast):
    install_base_classes(ast)
    build_inheritance_graph(ast)
    check_for_undefined_classes()
    impede_inheritance_from_base_classes()
    check_for_inheritance_cycles()
    for cl in classes_dict.values():
        check_variable_scopes(cl)


