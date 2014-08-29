from compiler.parser import parser
from compiler.parser import Class, Method, Attr, Object, Int, Str, Block, Assign, \
        Dispatch, StaticDispatch, SelfDispatch, Plus, Sub, Mult, Div, Lt, Le, Eq, \
        If, While, Let, Case, New, Isvoid, Neg, Not

from compiler import semant

import pytest


def test_base_classes_added_to_ast():
    ast = [Class('A', 'Object', [])]
    semant.install_base_classes(ast)
    final_ast_classes = {cl.name for cl in ast}
    assert 'A' in final_ast_classes
    assert 'Object' in final_ast_classes
    assert 'String' in final_ast_classes
    assert 'Int' in final_ast_classes
    assert 'Bool' in final_ast_classes


def test_inheritance_graph_builds_correctly():
    ast = [Class('A', 'Top', []), Class('Top', 'Object', [])]
    semant.build_inheritance_graph(ast)
    semant.check_for_undefined_classes()
    assert 'A' in semant.inheritance_graph['Top']
    assert 'Top' in semant.inheritance_graph['Object']


def test_undefined_class_rewires_inheritance():
    ast = [Class('A', 'Top', [])]
    semant.build_inheritance_graph(ast)
    semant.check_for_undefined_classes()
    assert 'A' in semant.inheritance_graph['Object']


def test_class_cannot_inherit_from_base_types():
    ast = [Class('A', 'String', [])]
    semant.build_inheritance_graph(ast)
    with pytest.raises(semant.SemantError) as e:
        semant.impede_inheritance_from_base_classes()
    assert str(e.value) == "Class A cannot inherit from base class String"


def test_double_class_definition_triggers_error():
    ast = [Class('A', 'B', []), Class('A', 'Object', []), Class('B', 'Object', [])]
    with pytest.raises(semant.SemantError) as e:
        semant.build_inheritance_graph(ast)
    assert str(e.value) == "class A already defined"


def test_classes_inheriting_correctly_validates():
    ast = [Class('A', 'B', []), Class('B', 'Object', [])]
    semant.build_inheritance_graph(ast)
    semant.check_for_inheritance_cycles()


def test_classes_inheriting_from_each_other_fails_validation():
    ast = [Class('A', 'B', []), Class('B', 'A', []), Class("C", "Object", [])]
    semant.build_inheritance_graph(ast)
    with pytest.raises(semant.SemantError) as e:
        semant.check_for_inheritance_cycles()
    assert str(e.value) == "B involved in an inheritance cycle." or str(e.value) == "A involved in an inheritance cycle."


def test_class_with_double_defined_attrs():
    astclass = Class('A', 'Object', [
                     Attr('attr1', 'AttrType', None),
                     Attr('attr1', 'AttrType', None),
                     ])
    with pytest.raises(semant.SemantError) as e:
        semant.check_scopes_and_infer_return_types(astclass)
    assert str(e.value) == "attribute attr1 is already defined"


def test_class_with_double_defined_methods():
    astclass = Class('A', 'Object', [
                     Method('funk', [], 'ReturnType', Int(1)),
                     Method('funk', [], 'ReturnType', Int(2)),
                     ])
    with pytest.raises(semant.SemantError) as e:
        semant.check_scopes_and_infer_return_types(astclass)
    assert str(e.value) == "method funk is already defined"


def test_class_with_method_with_double_defined_formals():
    astclass = Class('A', 'Object', [
                     Method('funk', [('x', 'X'), ('x', 'X')], 'ReturnType', Object('x')),
                     ])
    with pytest.raises(semant.SemantError) as e:
        semant.check_scopes_and_infer_return_types(astclass)
    assert str(e.value) == "formal x in method funk is already defined"


def test_method_returning_a_variable_not_in_scope():
    astclass = Class('A', 'Object', [
                     Method('funk', [], 'ReturnType', Object('returnvalue')),
                     ])
    with pytest.raises(semant.SemantError) as e:
        semant.check_scopes_and_infer_return_types(astclass)
    assert str(e.value) == "variable returnvalue not in scope"


def test_method_returning_a_variable_scoped_through_let():
    astclass = Class('A', 'Object', [
                     Method('funk', [], 'ReturnType',
                        Let('x', 'TypeX', None, Plus(Object('x'), Int(1)))
                             ),
                     ])
    semant.check_scopes_and_infer_return_types(astclass)


def test_method_returning_a_variable_not_scoped_through_let():
    astclass = Class('A', 'Object', [
                     Method('funk', [], 'ReturnType',
                        Let('y', 'TypeX', None, Plus(Object('x'), Int(1)))
                             ),
                     ])
    with pytest.raises(semant.SemantError) as e:
        semant.check_scopes_and_infer_return_types(astclass)
    assert str(e.value) == "variable x not in scope"


def test_method_returning_a_variable_scoped_through_attr():
    astclass = Class('A', 'Object', [
                     Attr('attr1', 'AttrType', None),
                     Method('returnattr1', [], 'AttrType', Object('attr1')),
                     ])
    semant.check_scopes_and_infer_return_types(astclass)


def test_method_returning_a_variable_scoped_through_formal():
    astclass = Class('A', 'Object', [
                     Method('returnarg', [('arg', 'ArgT')], 'AttrType', Object('arg')),
                     ])
    semant.check_scopes_and_infer_return_types(astclass)


def test_inherited_attributes_cannot_be_redefined():
    ast = [
            Class('A', 'Object', [
                 Attr('attr1', 'AttrType', None),
            ]),
            Class('B', 'A', [
                 Attr('attr1', 'AnotherType', None),
            ])
         ]
    semant.install_base_classes(ast)
    semant.build_inheritance_graph(ast)
    with pytest.raises(semant.SemantError) as e:
        semant.expand_inherited_classes()
    assert str(e.value) == "Attribute cannot be redefined in child class B"


def test_inherited_methods_cannot_redefine_signatures():
    ast = [
            Class('A', 'Object', [
                Method('returnarg', [('arg', 'ArgT')], 'AttrType', Object('arg')),
            ]),
            Class('B', 'A', [
                Method('returnarg', [('arg', 'ArgT')], 'String', Str('abc')),
            ])
         ]
    semant.install_base_classes(ast)
    semant.build_inheritance_graph(ast)
    with pytest.raises(semant.SemantError) as e:
        semant.expand_inherited_classes()
    assert str(e.value) == "Redefined method returnarg cannot change arguments or return type of the parent method"


def test_inheritance_expansion_is_applied_correctly():
    astchild = Class('B', 'A', [])
    ast = [
            astchild,
            Class('A', 'Object', [
                Attr('attr1', 'AnotherType', None),
                Method('returnattr', [], 'AnotherType', Object('attr1')),
            ])
         ]
    semant.install_base_classes(ast)
    semant.build_inheritance_graph(ast)
    semant.expand_inherited_classes()
    assert astchild.feature_list[0].name == "attr1"
    assert astchild.feature_list[1].name == "returnattr"


def test_attributes_are_type_checked_on_declaration():
    ast = [
            Class('TypeA', 'Object', []),
            Class('A', 'Object', [
               Attr('attr1', 'TypeA', None),
               Attr('attr2', 'Int', Object('attr1')),
            ])
         ]
    semant.install_base_classes(ast)
    semant.build_inheritance_graph(ast)
    for cl in ast:
        semant.check_scopes_and_infer_return_types(cl)
    with pytest.raises(semant.SemantError) as e:
        for cl in ast:
            semant.type_check(cl)
    assert str(e.value) == "Inferred type TypeA for attribute attr2 does not conform to declared type Int"


def test_attributes_are_type_checked():
    ast = [
            Class('A', 'Object', [
               Attr('attr1', 'Int', Int(2)),
               Attr('attr2', 'String', Object('attr1')),
            ])
         ]
    semant.install_base_classes(ast)
    semant.build_inheritance_graph(ast)
    semant.check_scopes_and_infer_return_types(ast[0])
    with pytest.raises(semant.SemantError) as e:
        semant.type_check(ast[0])
    assert str(e.value) == "Inferred type Int for attribute attr2 does not conform to declared type String"


def test_methods_have_formals_with_known_types():
    ast = [
            Class('A', 'Object', [
                Method('returnattr', [('x', 'UnknownType')], 'AnotherType', Int(1)),
            ])
         ]
    semant.install_base_classes(ast)
    semant.build_inheritance_graph(ast)
    semant.check_scopes_and_infer_return_types(ast[0])
    with pytest.raises(semant.SemantError) as e:
        semant.type_check(ast[0])
    assert str(e.value) == "formal x has a undefined type"


def test_methods_are_type_checked():
    ast = [
            Class('A', 'Object', [
                Method('returnattr', [], 'AnotherType', Int(1)),
            ])
         ]
    semant.install_base_classes(ast)
    semant.build_inheritance_graph(ast)
    semant.check_scopes_and_infer_return_types(ast[0])
    with pytest.raises(semant.SemantError) as e:
        semant.type_check(ast[0])
    assert str(e.value) == "Inferred type Int for method returnattr does not conform to declared type AnotherType"


def test_correct_lca_on_if_statements_validates():
    ast = [
            Class('TypeA', 'Object', []),
            Class('TypeB', 'Object', []),
            Class('SubTypeAA', 'TypeA', []),
            Class('SubTypeAB', 'TypeA', []),
            Class('A', 'Object', [
               Attr('attr1', 'SubTypeAA', None),
               Attr('attr2', 'SubTypeAB', None),
               Attr('attr3', 'TypeA', If(Not(Isvoid(Object('attr1'))), Object('attr1'), Object('attr2')))
            ])
         ]
    semant.install_base_classes(ast)
    semant.build_inheritance_graph(ast)
    for cl in ast:
        semant.check_scopes_and_infer_return_types(cl)
    for cl in ast:
        semant.type_check(cl)


def test_incorrect_lca_on_if_statements_fails():
    ast = [
            Class('TypeA', 'Object', []),
            Class('TypeB', 'Object', []),
            Class('SubTypeAA', 'TypeA', []),
            Class('SubTypeAB', 'TypeA', []),
            Class('A', 'Object', [
               Attr('attr1', 'SubTypeAA', None),
               Attr('attr2', 'SubTypeAB', None),
               Attr('attr3', 'TypeB', If(Isvoid(Object('attr1')), Object('attr1'), Object('attr2')))
            ])
         ]
    semant.install_base_classes(ast)
    semant.build_inheritance_graph(ast)
    for cl in ast:
        semant.check_scopes_and_infer_return_types(cl)
    with pytest.raises(semant.SemantError) as e:
        for cl in ast:
            semant.type_check(cl)
    assert str(e.value) == "Inferred type TypeA for attribute attr3 does not conform to declared type TypeB"


def test_correct_lca_on_case_statements_validates():
    ast = [
            Class('TypeA', 'Object', []),
            Class('TypeB', 'Object', []),
            Class('SubTypeAA', 'TypeA', []),
            Class('SubTypeAB', 'TypeA', []),
            Class('SubTypeAC', 'TypeA', []),
            Class('SubTypeAAA', 'SubTypeAA', []),
            Class('A', 'Object', [
               Attr('attr1', 'SubTypeAA', None),
               Attr('attr2', 'SubTypeAB', None),
               Attr('attr3', 'SubTypeAAA', None),
               Attr('attr4', 'TypeA',
                   Case(Int(1), [
                        ('x', 'X', Object('attr1')),
                        ('x', 'Y', Object('attr2')),
                        ('x', 'Z', Object('attr3')),
                       ])
                   )
            ])
         ]
    semant.install_base_classes(ast)
    semant.build_inheritance_graph(ast)
    for cl in ast:
        semant.check_scopes_and_infer_return_types(cl)
    for cl in ast:
        semant.type_check(cl)


def test_incorrect_lca_on_case_statements_fails():
    ast = [
            Class('TypeA', 'Object', []),
            Class('TypeB', 'Object', []),
            Class('SubTypeAA', 'TypeA', []),
            Class('SubTypeAB', 'TypeA', []),
            Class('SubTypeAC', 'TypeA', []),
            Class('SubTypeAAA', 'SubTypeAA', []),
            Class('A', 'Object', [
               Attr('attr1', 'SubTypeAA', None),
               Attr('attr2', 'SubTypeAB', None),
               Attr('attr3', 'TypeB', None),
               Attr('attr4', 'TypeA',
                   Case(Int(1), [
                        ('x', 'X', Object('attr1')),
                        ('x', 'Y', Object('attr2')),
                        ('x', 'Z', Object('attr3')),
                       ])
                   )
            ])
         ]
    semant.install_base_classes(ast)
    semant.build_inheritance_graph(ast)
    for cl in ast:
        semant.check_scopes_and_infer_return_types(cl)
    with pytest.raises(semant.SemantError) as e:
        for cl in ast:
            semant.type_check(cl)
    assert str(e.value) == "Inferred type Object for attribute attr4 does not conform to declared type TypeA"


def test_assignments_are_type_checked():
    ast = [
            Class('A', 'Object', [
               Attr('x', 'Int', None),
               Method('funk', [], 'Int',
                   Block([
                      Assign(Object('x'), Str("jjj")),
                      Int(2)
                      ])
               ),
            ])
    ]
    semant.install_base_classes(ast)
    semant.build_inheritance_graph(ast)
    for cl in ast:
        semant.check_scopes_and_infer_return_types(cl)
    with pytest.raises(semant.SemantError) as e:
        for cl in ast:
            semant.type_check(cl)
    assert str(e.value) == "The inferred type String for x is not conformant to declared type Int"


def test_if_statements_require_booleans():
    ast = [
            Class('A', 'Object', [
               Method('funk', [], 'Int',
                   Block([
                      If(Int(3), Int(2), Int(1)),
                      Int(2)
                      ])
               ),
            ])
    ]
    semant.install_base_classes(ast)
    semant.build_inheritance_graph(ast)
    for cl in ast:
        semant.check_scopes_and_infer_return_types(cl)
    with pytest.raises(semant.SemantError) as e:
        for cl in ast:
            semant.type_check(cl)
    assert str(e.value) == "If statements must have boolean conditions"


def test_if_statements_get_booleans_from_cmp_ops():
    ast = [
            Class('A', 'Object', [
               Method('funk', [], 'Int',
                   Block([
                      If(Lt(Int(3), Int(4)), Int(2), Int(1)),
                      Int(2)
                      ])
               ),
            ])
    ]
    semant.install_base_classes(ast)
    semant.build_inheritance_graph(ast)
    for cl in ast:
        semant.check_scopes_and_infer_return_types(cl)
    for cl in ast:
        semant.type_check(cl)


def test_let_statements_initialized_with_wrong_type_fails():
    ast = [
            Class('A', 'Object', [
               Method('funk', [], 'Int',
                    Let('x', 'Int', Str("jjj"), Int(2))
               ),
            ])
    ]
    semant.install_base_classes(ast)
    semant.build_inheritance_graph(ast)
    for cl in ast:
        semant.check_scopes_and_infer_return_types(cl)
    with pytest.raises(semant.SemantError) as e:
        for cl in ast:
            semant.type_check(cl)
    assert str(e.value) == "The inferred type String for let init is not conformant to declared type Int"


def test_let_statements_initialized_with_correct_type_validates():
    ast = [
            Class('A', 'Object', [
               Method('funk', [], 'Int',
                    Let('x', 'Int', Int(1), Int(2))
               ),
            ])
    ]
    semant.install_base_classes(ast)
    semant.build_inheritance_graph(ast)
    for cl in ast:
        semant.check_scopes_and_infer_return_types(cl)
    for cl in ast:
        semant.type_check(cl)


def test_static_dispatch_to_inexistent_classes_are_invalid():
    ast = [
            Class('A', 'Object', [
               Attr('support', 'SupportClass', None),
               Method('funk', [], 'Int',
                   StaticDispatch(Object("support"), "InexistentClass", "method", [])
               ),
            ])
    ]
    semant.install_base_classes(ast)
    semant.build_inheritance_graph(ast)
    semant.expand_inherited_classes()
    for cl in ast:
        semant.check_scopes_and_infer_return_types(cl)
    with pytest.raises(semant.SemantError) as e:
        for cl in ast:
            semant.type_check(cl)
    assert str(e.value) == "Static dispatch expression (before @Type) does not conform to declared type InexistentClass"


def test_static_dispatch_to_existent_classes_outside_inheritance_tree_are_invalid():
    ast = [
            Class('SupportClass', 'Object', []),
            Class('NoSupportClass', 'Object', []),
            Class('A', 'Object', [
               Attr('support', 'SupportClass', None),
               Method('funk', [], 'Int',
                   StaticDispatch(Object("support"), "NoSupportClass", "method", [])
               ),
            ])
    ]
    semant.install_base_classes(ast)
    semant.build_inheritance_graph(ast)
    semant.expand_inherited_classes()
    for cl in ast:
        semant.check_scopes_and_infer_return_types(cl)
    with pytest.raises(semant.SemantError) as e:
        for cl in ast:
            semant.type_check(cl)
    assert str(e.value) == "Static dispatch expression (before @Type) does not conform to declared type NoSupportClass"


def test_static_dispatch_to_existent_classes_inside_inheritance_tree_are_valid():
    ast = [
            Class('SupportClass', 'Object', [
                Method('method', [], 'Int', Int(1)),
                ]),
            Class('SupportSubClass', 'SupportClass', []),
            Class('A', 'Object', [
               Attr('support', 'SupportSubClass', None),
               Method('funk', [], None,
                   StaticDispatch(Object("support"), "SupportClass", "method", [])
               ),
            ])
    ]
    semant.install_base_classes(ast)
    semant.build_inheritance_graph(ast)
    semant.expand_inherited_classes()
    for cl in ast:
        semant.check_scopes_and_infer_return_types(cl)
    for cl in ast:
        semant.type_check(cl)


def test_dispatch_to_inexistent_method_crashes():
    ast = [
            Class('SupportClass', 'Object', [
                Method('method', [], 'Int', Int(1)),
                ]),
            Class('A', 'Object', [
               Attr('support', 'SupportClass', None),
               Method('funk', [], None,
                   Dispatch(Object("support"), "ghostmethod", [])
               ),
            ])
    ]
    semant.install_base_classes(ast)
    semant.build_inheritance_graph(ast)
    semant.expand_inherited_classes()
    for cl in ast:
        semant.check_scopes_and_infer_return_types(cl)
    with pytest.raises(semant.SemantError) as e:
        for cl in ast:
            semant.type_check(cl)
    assert str(e.value) == "Tried to call an undefined method in class SupportClass"


def test_dispatch_to_existent_method_with_wrong_args_gives_error():
    ast = [
            Class('SupportClass', 'Object', [
                Method('addOne', [('x', 'Int')], 'Int', Plus(Object('x'), Int(1))),
                ]),
            Class('A', 'Object', [
               Attr('support', 'SupportClass', None),
               Method('funk', [], None,
                   Dispatch(Object("support"), "addOne", [])
               ),
            ])
    ]
    semant.install_base_classes(ast)
    semant.build_inheritance_graph(ast)
    semant.expand_inherited_classes()
    for cl in ast:
        semant.check_scopes_and_infer_return_types(cl)
    with pytest.raises(semant.SemantError) as e:
        for cl in ast:
            semant.type_check(cl)
    assert str(e.value) == "Tried to call method addOne in class SupportClass with wrong number of arguments"


def test_dispatch_to_existent_method_with_wrong_arg_types_gives_error():
    ast = [
            Class('SupportClass', 'Object', [
                Method('addOne', [('x', 'Int')], 'Int', Plus(Object('x'), Int(1))),
                ]),
            Class('A', 'Object', [
               Attr('support', 'SupportClass', None),
               Method('funk', [], None,
                   Dispatch(Object("support"), "addOne", [Str("CRASH")])
               ),
            ])
    ]
    semant.install_base_classes(ast)
    semant.build_inheritance_graph(ast)
    semant.expand_inherited_classes()
    for cl in ast:
        semant.check_scopes_and_infer_return_types(cl)
    with pytest.raises(semant.SemantError) as e:
        for cl in ast:
            semant.type_check(cl)
    assert str(e.value) == "Argument String passed to method addOne in class SupportClass is not conformant to its Int declaration"


def test_dispatch_to_existent_method_with_right_args_succeeds():
    ast = [
            Class('SupportClass', 'Object', [
                Method('addOne', [('x', 'Int')], 'Int', Plus(Object('x'), Int(1))),
                ]),
            Class('A', 'Object', [
               Attr('support', 'SupportClass', None),
               Method('funk', [], None,
                   Dispatch(Object("support"), "addOne", [Int(2)])
               ),
            ])
    ]
    semant.install_base_classes(ast)
    semant.build_inheritance_graph(ast)
    semant.expand_inherited_classes()
    for cl in ast:
        semant.check_scopes_and_infer_return_types(cl)
    for cl in ast:
        semant.type_check(cl)


def test_while_statements_require_booleans():
    ast = [
            Class('A', 'Object', [
               Method('funk', [], 'Int',
                   Block([
                      While(Int(3), Int(1)),
                      Int(2)
                      ])
               ),
            ])
    ]
    semant.install_base_classes(ast)
    semant.build_inheritance_graph(ast)
    for cl in ast:
        semant.check_scopes_and_infer_return_types(cl)
    with pytest.raises(semant.SemantError) as e:
        for cl in ast:
            semant.type_check(cl)
    assert str(e.value) == "While statement must have boolean conditions"


def test_arithmentic_ops_require_integers():
    ast = [
            Class('A', 'Object', [
               Method('funk', [], 'Int',
                   Block([
                      Plus(Str("NOO"), Int(2))
                      ])
               ),
            ])
    ]
    semant.install_base_classes(ast)
    semant.build_inheritance_graph(ast)
    for cl in ast:
        semant.check_scopes_and_infer_return_types(cl)
    with pytest.raises(semant.SemantError) as e:
        for cl in ast:
            semant.type_check(cl)
    assert str(e.value) == "Arithmetic operations require integers"


def test_comparison_between_basic_type_and_not_fails():
    ast = [
            Class('A', 'Object', [
               Method('funk', [], None,
                   Block([
                      If(Eq(Str("NOO"), Int(1)), Int(2), Int(3))
                      ])
               ),
            ])
    ]
    semant.install_base_classes(ast)
    semant.build_inheritance_graph(ast)
    for cl in ast:
        semant.check_scopes_and_infer_return_types(cl)
    with pytest.raises(semant.SemantError) as e:
        for cl in ast:
            semant.type_check(cl)
    assert str(e.value) == "Comparison is only possible among same base types"


