from .parser import Class, Method, Attr, Object, Int, Str, Block, Assign, \
        Dispatch, StaticDispatch, Plus, Sub, Mult, Div, Lt, Le, Eq, \
        If, While, Let, Case, New, Isvoid, Neg, Not

from collections import defaultdict, MutableMapping, Set
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
        Method('abort', [], 'Object', None),  # aborts the program
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
        if cl.name == "Object":
            continue  # Object has no parent
        inheritance_graph[cl.parent].add(cl.name)


def check_for_undefined_classes():
    initial_parents = list(inheritance_graph.keys())
    for parentc in initial_parents:
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


class VariablesScopeSet(Set):
    """dictionary of varnames that represent variable scope in the ast"""

    def __init__(self):
        self.store = [set()]

    def __iter__(self):
        raise NotImplementedError

    def __contains__(self, value):
        for scope in self.store[::-1]:
            if value in scope:
                return True
        return False

    def __len__(self):
        raise NotImplementedError

    def add(self, value):
        """just call add on the last set"""
        self.store[-1].add(value)

    def new_scope(self):
        self.store.append(set())

    def destroy_scope(self):
        del self.store[-1]


def check_scopes_and_infer_return_types(cl):
    # this function does scope checking and type inference together because
    # the latter is dependent on the first
    variable_scopes = VariablesScopeDict()
    # in COOL methods are not in the same variable scope, which means we can
    # have methods with same name as variables
    attr_seen = set()
    method_seen = set()
    for feature in cl.feature_list:
        if isinstance(feature, Attr):
            if feature.name in attr_seen:
                raise SemantError("attribute %s is already defined" % feature.name)
            attr_seen.add(feature.name)

            if feature.type == "SELF_TYPE":
                realtype = cl.name
            else:
                realtype = feature.type

            variable_scopes[feature.name] = realtype
            traverse_expression(feature.body, variable_scopes, cl)
        elif isinstance(feature, Method):
            if feature.name in method_seen:
                raise SemantError("method %s is already defined" % feature.name)
            method_seen.add(feature.name)
            variable_scopes.new_scope()

            formals_seen = set()
            for formal in feature.formal_list:
                if formal in formals_seen:
                    raise SemantError("formal %s in method %s is already defined" % (formal[0], feature.name))
                formals_seen.add(formal)
                variable_scopes[formal[0]] = formal[1]

            traverse_expression(feature.body, variable_scopes, cl)
            variable_scopes.destroy_scope()


def lowest_common_ancestor(*classes):
    """return the lowest common parent of cl1 and cl2"""
    def ascend_tree(cl):
        yield cl.name
        if cl.parent:
            yield from ascend_tree(classes_dict[cl.parent])

    inheritance_paths = []
    for cl in classes:
        path = list(ascend_tree(cl))
        path.reverse()
        inheritance_paths.append(path)

    smallest_inheritance_path_length = min(len(x) for x in inheritance_paths)

    for step in range(smallest_inheritance_path_length):
        inheritance_points = [x[step] for x in inheritance_paths]
        if len(set(inheritance_points)) > 1:
            return inheritance_paths[0][step-1]  # any would do

    # if we are here, means objects have the same type
    return classes[0].name


def traverse_expression(expression, variable_scopes, cl):
    if isinstance(expression, Isvoid):
        traverse_expression(expression.body, variable_scopes, cl)
        expression.return_type = "Bool"
    elif any(isinstance(expression, X) for X in [Eq, Lt, Le]):
        traverse_expression(expression.first, variable_scopes, cl)
        traverse_expression(expression.second, variable_scopes, cl)
        expression.return_type = "Bool"
    elif isinstance(expression, Neg):
        traverse_expression(expression.body, variable_scopes, cl)
        expression.return_type = "Bool"
    elif isinstance(expression, Not):
        traverse_expression(expression.body, variable_scopes, cl)
        expression.return_type = "Bool"
    elif any(isinstance(expression, X) for X in [Plus, Sub, Mult, Div]):
        traverse_expression(expression.first, variable_scopes, cl)
        traverse_expression(expression.second, variable_scopes, cl)
        expression.return_type = "Int"
    elif isinstance(expression, While):
        traverse_expression(expression.predicate, variable_scopes, cl)
        traverse_expression(expression.body, variable_scopes, cl)
    elif isinstance(expression, Let):
        # LET creates a new scope
        variable_scopes.new_scope()
        variable_scopes[expression.object] = expression.type
        traverse_expression(expression.init, variable_scopes, cl)
        traverse_expression(expression.body, variable_scopes, cl)
        variable_scopes.destroy_scope()
        expression.return_type = expression.body.return_type
    elif isinstance(expression, Block):
        last_type = None
        for expr in expression.body:
            traverse_expression(expr, variable_scopes, cl)
            last_type = getattr(expr, 'return_type', None)
        expression.return_type = last_type
    elif isinstance(expression, Assign):
        traverse_expression(expression.body, variable_scopes, cl)
        traverse_expression(expression.name, variable_scopes, cl)
    elif isinstance(expression, Dispatch) or isinstance(expression, StaticDispatch):
        traverse_expression(expression.body, variable_scopes, cl)
        for expr in expression.expr_list:
            traverse_expression(expr, variable_scopes, cl)

        # REDUNDANT code, copied from type_check because we need to infer
        # the dispatch return type from the called method type

        # in case it's self, use current class name
        if expression.body == "self":
            bodycln = cl.name
        else:
            bodycln = expression.body.return_type

        called_method = None
        if bodycln in classes_dict:
            bodycl = classes_dict[bodycln]
            for feature in bodycl.feature_list:
                if isinstance(feature, Method) and feature.name == expression.method:
                    called_method = feature
        if not called_method:
            raise SemantError("Tried to call the undefined method %s in class %s" % (expression.method, bodycl.name))

        if called_method.return_type == "SELF_TYPE":
            method_type = bodycl.name
        else:
            method_type = called_method.return_type

        expression.return_type = method_type
    elif isinstance(expression, If):
        traverse_expression(expression.predicate, variable_scopes, cl)
        traverse_expression(expression.then_body, variable_scopes, cl)
        traverse_expression(expression.else_body, variable_scopes, cl)
        then_type = classes_dict[expression.then_body.return_type]
        else_type = classes_dict[expression.else_body.return_type]
        ret_type = lowest_common_ancestor(then_type, else_type)
        expression.return_type = ret_type
    elif isinstance(expression, Case):
        traverse_expression(expression.expr, variable_scopes, cl)
        branch_types = []
        for case in expression.case_list:
            variable_scopes.new_scope()  # every branch of case has its own scope
            variable_scopes[case[0]] = case[1]
            traverse_expression(case[2], variable_scopes, cl)
            branch_types.append(classes_dict[case[2].return_type])
        expression.return_type = lowest_common_ancestor(*branch_types)
    elif isinstance(expression, Object):
        if expression.name == "self":
            expression.return_type = cl.name
            return
        if expression.name not in variable_scopes:
            raise SemantError("variable %s not in scope" % expression.name)
        expression.return_type = variable_scopes[expression.name]
    elif isinstance(expression, New):
        if expression.type == "SELF_TYPE":
            expression.return_type = cl.name
            return
        expression.return_type = expression.type
    elif isinstance(expression, Int):
        expression.return_type = "Int"
    elif isinstance(expression, Str):
        expression.return_type = "String"


def expand_inherited_classes(start_class="Object"):
    """apply inheritance rules through the class graph"""
    cl = classes_dict[start_class]
    if cl.parent:
        parentcl = classes_dict[cl.parent]

        # Not performant, but cleaner
        attr_set_in_child = {i for i in cl.feature_list if isinstance(i, Attr)}
        attr_set_in_parent = {i for i in parentcl.feature_list if isinstance(i, Attr)}

        for attr in attr_set_in_child:
            for pattr in attr_set_in_parent:
                if attr.name == pattr.name:
                    raise SemantError("Attribute cannot be redefined in child class %s" % cl.name)

        method_set_in_child = [i for i in cl.feature_list if isinstance(i, Method)]
        method_set_in_parent = [i for i in parentcl.feature_list if isinstance(i, Method)]

        def extract_signatures(method_set):
            method_signatures = {}
            for method in method_set:
                method_signatures[method.name] = {}
                for formal in method.formal_list:
                    method_signatures[method.name][formal[0]] = formal[1]
                method_signatures[method.name]['return'] = method.return_type
            return method_signatures

        method_signatures_for_child = extract_signatures(method_set_in_child)
        method_signatures_for_parent = extract_signatures(method_set_in_parent)

        methods_in_child = set()
        for method in method_set_in_child:
            methods_in_child.add(method.name)
            if method.name in method_signatures_for_parent:
                parent_signature = method_signatures_for_parent[method.name]
                child_signature = method_signatures_for_child[method.name]
                if parent_signature != child_signature:
                    raise SemantError("Redefined method %s cannot change arguments or return type of the parent method" % method.name)

        # finished checks, now apply inheritance by simply copying definitions
        for attr in attr_set_in_parent:
            cl.feature_list.append(attr)
        for method in method_set_in_parent:
            if method.name not in methods_in_child:
                cl.feature_list.append(method)

    # descend down the inheritance tree, applying the same function
    all_children = inheritance_graph[start_class]
    for child in all_children:
        expand_inherited_classes(child)


def is_conformant(childclname, parentclname):
    """check whether childcl is a descendent of parentcl"""
    if childclname == parentclname:
        return True
    for clname in inheritance_graph[parentclname]:
        if is_conformant(childclname, clname):
            return True
    return False


def type_check(cl):
    """make sure the inferred types match the declared types"""
    for feature in cl.feature_list:
        if isinstance(feature, Attr):
            if feature.type == "SELF_TYPE":
                realtype = cl.name
            else:
                realtype = feature.type

            if feature.body:
                type_check_expression(feature.body, cl)
                childcln = feature.body.return_type
                parentcln = realtype
                if not is_conformant(childcln, parentcln):
                    raise SemantError("Inferred type %s for attribute %s does not conform to declared type %s" % (childcln, feature.name, parentcln))
        elif isinstance(feature, Method):
            for formal in feature.formal_list:
                if formal[1] == "SELF_TYPE":
                    raise SemantError("formal %s cannot have type SELF_TYPE" % formal[0])
                elif formal[1] not in classes_dict:
                    raise SemantError("formal %s has a undefined type" % formal[0])

            if feature.return_type == "SELF_TYPE":
                realrettype = cl.name
            else:
                realrettype = feature.return_type

            if feature.body is None:
                # for internal classes, some methods body are not defined
                # assume they return SELF_TYPE
                if feature.return_type == "SELF_TYPE":
                    returnedcln = cl.name
                else:
                    returnedcln = feature.return_type
            else:
                type_check_expression(feature.body, cl)
                returnedcln = feature.body.return_type

            declaredcln = realrettype
            if not is_conformant(returnedcln, declaredcln):
                raise SemantError("Inferred type %s for method %s does not conform to declared type %s" % (returnedcln, feature.name, declaredcln))



def type_check_expression(expression, cl):
    """make sure types validate at any point in the ast"""
    if isinstance(expression, Case):
        type_check_expression(expression.expr, cl)
        for case in expression.case_list:
            type_check_expression(case[2], cl)
    elif isinstance(expression, Assign):
        type_check_expression(expression.body, cl)
        if not is_conformant(expression.body.return_type, expression.name.return_type):
            raise SemantError("The inferred type %s for %s is not conformant to declared type %s" % (expression.body.return_type, expression.name.name, expression.name.return_type))
    elif isinstance(expression, If):
        type_check_expression(expression.predicate, cl)
        type_check_expression(expression.then_body, cl)
        type_check_expression(expression.else_body, cl)
        if expression.predicate.return_type != "Bool":
            raise SemantError("If statements must have boolean conditions")
    elif isinstance(expression, Let):
        type_check_expression(expression.init, cl)
        if expression.init:  # some let expression auto-initialize with default values
            if not is_conformant(expression.init.return_type, expression.type):
                raise SemantError("The inferred type %s for let init is not conformant to declared type %s" % (expression.init.return_type, expression.type))
    elif isinstance(expression, Block):
        for line in expression.body:
            type_check_expression(line, cl)
    elif isinstance(expression, Dispatch) or isinstance(expression, StaticDispatch):
        type_check_expression(expression.body, cl)
        # in case it's self, use current class name
        if expression.body == "self":
            bodycln = cl.name
        else:
            bodycln = expression.body.return_type
        if isinstance(expression, StaticDispatch):
            # additional check on static dispatch
            if not is_conformant(bodycln, expression.type):
                raise SemantError("Static dispatch expression (before @Type) does not conform to declared type {}".format(expression.type))

        called_method = None
        if bodycln in classes_dict:
            bodycl = classes_dict[bodycln]
            for feature in bodycl.feature_list:
                if isinstance(feature, Method) and feature.name == expression.method:
                    called_method = feature
        if not called_method:
            raise SemantError("Tried to call the undefined method %s in class %s" % (expression.method, bodycl.name))
        if len(expression.expr_list) != len(called_method.formal_list):
            raise SemantError("Tried to call method {} in class {} with wrong number of arguments".format(called_method.name, bodycl.name))
        else:
            # check conformance of arguments
            for expr, formal in zip(expression.expr_list, called_method.formal_list):
                if not is_conformant(expr.return_type, formal[1]):
                    raise SemantError("Argument {} passed to method {} in class {} is not conformant to its {} declaration".format(expr.return_type, called_method.name, bodycl.name, formal[1]))
    elif isinstance(expression, While):
        type_check_expression(expression.predicate, cl)
        type_check_expression(expression.body, cl)
        if expression.predicate.return_type != "Bool":
            raise SemantError("While statement must have boolean conditions")
    elif isinstance(expression, Isvoid):
        type_check_expression(expression.body, cl)
    elif isinstance(expression, Not):
        type_check_expression(expression.body, cl)
        if expression.body.return_type != "Bool":
            raise SemantError("Not statement require boolean values")
    elif isinstance(expression, Lt) or isinstance(expression, Le):
        type_check_expression(expression.first, cl)
        type_check_expression(expression.second, cl)
        if expression.first.return_type != "Int" or expression.second.return_type != "Int":
            raise SemantError("Non-integer arguments cannot be check with < == or <=")
    elif isinstance(expression, Neg):
        type_check_expression(expression.body, cl)
        if expression.body.return_type != "Int":
            raise SemantError("Negative statement require integer values")
    elif any(isinstance(expression, X) for X in [Plus, Sub, Mult, Div]):
        type_check_expression(expression.first, cl)
        type_check_expression(expression.second, cl)
        if expression.first.return_type != "Int" or expression.second.return_type != "Int":
            raise SemantError("Arithmetic operations require integers")
    elif isinstance(expression, Eq):
        type_check_expression(expression.first, cl)
        type_check_expression(expression.second, cl)
        type1 = expression.first.return_type
        type2 = expression.second.return_type
        if (type1 == "Int" and type2 == "Int") or \
           (type1 == "Bool" and type2 == "Bool") or \
           (type1 == "String" and type2 == "String"):
            pass  # comparing basic types together is ok
        else:
            raise SemantError("Comparison is only possible among same base types")


def semant(ast):
    install_base_classes(ast)
    build_inheritance_graph(ast)
    check_for_undefined_classes()
    impede_inheritance_from_base_classes()
    check_for_inheritance_cycles()
    expand_inherited_classes()
    for cl in classes_dict.values():
        check_scopes_and_infer_return_types(cl)
    for cl in classes_dict.values():
        type_check(cl)


