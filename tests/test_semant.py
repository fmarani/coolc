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
    with pytest.raises(semant.SemantError):
        semant.impede_inheritance_from_base_classes()


def test_double_class_definition_triggers_error():
    ast = [Class('A', 'B', []), Class('A', 'Object', []), Class('B', 'Object', [])]
    with pytest.raises(semant.SemantError):
        semant.build_inheritance_graph(ast)


def test_classes_inheriting_correctly_validates():
    ast = [Class('A', 'B', []), Class('B', 'Object', [])]
    semant.build_inheritance_graph(ast)
    semant.check_for_inheritance_cycles()


def test_classes_inheriting_from_each_other_fails_validation():
    ast = [Class('A', 'B', []), Class('B', 'A', []), Class("C", "Object", [])]
    semant.build_inheritance_graph(ast)
    with pytest.raises(semant.SemantError):
        semant.check_for_inheritance_cycles()


def test_class_with_double_defined_attrs():
    astclass = Class('A', 'Object', [
                     Attr('attr1', 'AttrType', None),
                     Attr('attr1', 'AttrType', None),
                     ])
    with pytest.raises(semant.SemantError):
        semant.check_scopes_and_infer_return_types(astclass)


def test_class_with_double_defined_methods():
    astclass = Class('A', 'Object', [
                     Method('funk', [], 'ReturnType', Object('returnvalue')),
                     Method('funk', [], 'ReturnType', Object('another')),
                     ])
    with pytest.raises(semant.SemantError):
        semant.check_scopes_and_infer_return_types(astclass)


def test_class_with_method_with_double_defined_formals():
    astclass = Class('A', 'Object', [
                     Method('funk', [('x', 'X'), ('x', 'X')], 'ReturnType', Object('x')),
                     ])
    with pytest.raises(semant.SemantError):
        semant.check_scopes_and_infer_return_types(astclass)


def test_method_returning_a_variable_not_in_scope():
    astclass = Class('A', 'Object', [
                     Method('funk', [], 'ReturnType', Object('returnvalue')),
                     ])
    with pytest.raises(semant.SemantError):
        semant.check_scopes_and_infer_return_types(astclass)


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
    with pytest.raises(semant.SemantError):
        semant.check_scopes_and_infer_return_types(astclass)


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
    with pytest.raises(semant.SemantError):
        semant.expand_inherited_classes()


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
    with pytest.raises(semant.SemantError):
        semant.expand_inherited_classes()


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


def test_correct_lca_on_if_statements_validates():
    ast = [
            Class('TypeA', 'Object', []),
            Class('TypeB', 'Object', []),
            Class('SubTypeAA', 'TypeA', []),
            Class('SubTypeAB', 'TypeA', []),
            Class('A', 'Object', [
               Attr('attr1', 'SubTypeAA', None),
               Attr('attr2', 'SubTypeAB', None),
               Attr('attr3', 'TypeA', If(Int(1), Object('attr1'), Object('attr2')))
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
               Attr('attr3', 'TypeB', If(Int(1), Object('attr1'), Object('attr2')))
            ])
         ]
    semant.install_base_classes(ast)
    semant.build_inheritance_graph(ast)
    for cl in ast:
        semant.check_scopes_and_infer_return_types(cl)
    with pytest.raises(semant.SemantError) as e:
        for cl in ast:
            semant.type_check(cl)
    assert str(e.value) == "Inferred type SubTypeAA for attribute attr3 does not conform to declared type TypeB"


def ntest_correct_lca_on_case_statements_validates():
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


