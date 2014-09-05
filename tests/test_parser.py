from compiler.parser import parser
from compiler.parser import Class, Method, Attr, Object, Int, Str, Block, Assign, \
        Dispatch, StaticDispatch, Plus, Sub, Mult, Div, Lt, Le, Eq, \
        If, While, Let, Case, New, Isvoid, Neg, Not

def test_empty_class_definition():
    program = "class A2I { };"
    expected = [Class('A2I', 'Object', [])]
    assert parser.parse(program) == expected


def test_class_definition_with_inherits():
    program = "class A inherits Top { };"
    expected = [Class('A', 'Top', [])]
    assert parser.parse(program) == expected


def test_class_with_uninitialized_attributes():
    program = """
    class A {
        attr1:AttrType;
        attr2: AttrType;
    };"""
    expected = [Class('A', 'Object',
                [
                    Attr('attr1', 'AttrType', None),
                    Attr('attr2', 'AttrType', None),
                ]
                )]
    assert parser.parse(program) == expected


def test_class_with_initialized_attributes():
    program = """
    class A {
        attr1:AttrType <- otherObj;
        attr2: AttrType <- initialObj;
    };"""
    expected = [Class('A', 'Object',
                [
                    Attr('attr1', 'AttrType', Object('otherObj')),
                    Attr('attr2', 'AttrType', Object('initialObj')),
                ]
                )]
    assert parser.parse(program) == expected


def test_class_with_method_without_formals():
    program = """class A { funk():ReturnType { returnvalue }; };"""
    expected = [Class('A', 'Object',
                [
                    Method('funk', [], 'ReturnType', Object('returnvalue')),
                ]
                )]
    assert parser.parse(program) == expected


def test_class_with_method_with_formals():
    program = """class A { funk(x:X, y:Y):ReturnType { x }; };"""
    expected = [Class('A', 'Object',
                [
                    Method('funk', [('x', 'X'), ('y', 'Y')], 'ReturnType', Object('x')),
                ]
                )]
    assert parser.parse(program) == expected


def test_class_with_method_returning_int():
    program = """class A { funk():ReturnType { 12 }; };"""
    expected = [Class('A', 'Object',
                [
                    Method('funk', [], 'ReturnType', Int(12)),
                ]
                )]
    assert parser.parse(program) == expected


def test_class_with_method_returning_str():
    program = """class A { funk():ReturnType { "blabla" }; };"""
    expected = [Class('A', 'Object',
                [
                    Method('funk', [], 'ReturnType', Str('blabla')),
                ]
                )]
    assert parser.parse(program) == expected


def test_class_with_method_with_block():
    program = """
    class A inherits WithVar {
       set_var(num : Int) : SELF_TYPE {
          {
                 self;
          }
       };
    };"""
    expected = [Class('A', 'WithVar',
                [
                    Method('set_var', [('num', 'Int')], 'SELF_TYPE', Block([Object('self')])),
                ]
                )]
    assert parser.parse(program) == expected


def test_simple_dispatch_with_no_args():
    program = """
    class A {
       funk():Type {
            obj.method()
       };
    };"""
    expected = [Class('A', 'Object',
                [
                    Method('funk', [], 'Type', Dispatch(Object('obj'), 'method', [])),
                ]
                )]
    assert parser.parse(program) == expected


def test_simple_dispatch_with_one_arg():
    program = """
    class A {
       funk():Type {
            obj.method(2)
       };
    };"""
    expected = [Class('A', 'Object',
                [
                    Method('funk', [], 'Type', Dispatch(Object('obj'), 'method', [Int(2)])),
                ]
                )]
    assert parser.parse(program) == expected


def test_simple_dispatch_with_multiple_args():
    program = """
    class A {
       funk():Type {
            obj.method(2, "blabla", x)
       };
    };"""
    expected = [Class('A', 'Object',
                [
                    Method('funk', [], 'Type', Dispatch(Object('obj'), 'method', [Int(2), Str('blabla'), Object('x')])),
                ]
                )]
    assert parser.parse(program) == expected


def test_static_dispatch_with_no_args():
    program = """
    class A {
       funk():Type {
            obj@Klass.method()
       };
    };"""
    expected = [Class('A', 'Object',
                [
                    Method('funk', [], 'Type', StaticDispatch(Object('obj'), 'Klass', 'method', [])),
                ]
                )]
    assert parser.parse(program) == expected


def test_self_dispatch_with_no_args():
    program = """
    class A {
       funk():Type {
            method()
       };
    };"""
    expected = [Class('A', 'Object',
                [
                    Method('funk', [], 'Type', Dispatch('self', 'method', [])),
                ]
                )]
    assert parser.parse(program) == expected


def test_if_statements():
    program = """
    class A {
       funk():Type {
            if x < 0 then 1 else 2 fi
       };
    };"""
    expected = [Class('A', 'Object',
                [
                    Method('funk', [], 'Type',
                        If(Lt(Object('x'), Int(0)), Int(1), Int(2))
                     ),
                ]
                )]
    assert parser.parse(program) == expected


def test_while_statements():
    program = """
    class A {
       funk():Type {
            while x < 0 loop 1 pool
       };
    };"""
    expected = [Class('A', 'Object',
                [
                    Method('funk', [], 'Type',
                        While(Lt(Object('x'), Int(0)), Int(1))
                     ),
                ]
                )]
    assert parser.parse(program) == expected


def test_let_statement():
    program = """
    class A {
       funk():Type {
            let x:TypeX in x + 1
       };
    };"""
    expected = [Class('A', 'Object',
                [
                    Method('funk', [], 'Type',
                        Let('x', 'TypeX', None, Plus(Object('x'), Int(1)))
                     ),
                ]
                )]
    assert parser.parse(program) == expected


def test_let_statement_with_assignment():
    program = """
    class A {
       funk():Type {
            let x:TypeX <- 5 in x + 1
       };
    };"""
    expected = [Class('A', 'Object',
                [
                    Method('funk', [], 'Type',
                        Let('x', 'TypeX', Int(5), Plus(Object('x'), Int(1)))
                     ),
                ]
                )]
    assert parser.parse(program) == expected


def test_let_statement_with_two_vars():
    program = """
    class A {
       funk():Type {
            let x:TypeX <- 5,
                y:TypeY
                in x + 1
       };
    };"""
    expected = [Class('A', 'Object',
                [
                    Method('funk', [], 'Type',
                        Let('x', 'TypeX', Int(5),
                            Let('y', 'TypeY', None,
                                Plus(Object('x'), Int(1))
                             )
                        )
                     ),
                ]
                )]
    assert parser.parse(program) == expected


def test_let_statement_with_three_vars():
    program = """
    class A {
       funk():Type {
            let x:TypeX,
                y:TypeY <- 3,
                z:ZType <- (2+2) * 5
                in x + 1
       };
    };"""
    expected = [Class('A', 'Object',
                [
                    Method('funk', [], 'Type',
                        Let('x', 'TypeX', None,
                            Let('y', 'TypeY', Int(3),
                                Let('z', 'ZType', Mult(Plus(Int(2), Int(2)), Int(5)),
                                    Plus(Object('x'), Int(1))
                                )
                            )
                        )
                     ),
                ]
                )]
    assert parser.parse(program) == expected


def test_let_statement_with_two_vars_error_in_first():
    program = """
    class A {
       funk():Type {
            let x <- 5,
                x:TypeX <- 5
                in x + 1
       };
    };"""
    expected = [Class('A', 'Object',
                [
                    Method('funk', [], 'Type',
                        Let('x', 'TypeX', Int(5),
                                Plus(Object('x'), Int(1))
                        )
                     ),
                ]
                )]
    assert parser.parse(program) == expected


def test_new():
    program = """
    class A {
       funk():Type {
            new B
       };
    };"""
    expected = [Class('A', 'Object',
                [
                    Method('funk', [], 'Type',
                        New('B')
                     ),
                ]
                )]
    assert parser.parse(program) == expected


def test_isvoid():
    program = """
    class A {
       funk():Type {
            isvoid B
       };
    };"""
    expected = [Class('A', 'Object',
                [
                    Method('funk', [], 'Type',
                        Isvoid('B')
                     ),
                ]
                )]
    assert parser.parse(program) == expected


def test_case():
    program = """
    class A {
       funk():Type {
            case 1 of
                x:Int => 10;
                x:String => 9;
                x:Guru => 8;
            esac
       };
    };"""
    expected = [Class('A', 'Object',
                [
                    Method('funk', [], 'Type',
                        Case(Int(1),
                         [('x', 'Int', Int(10)),
                          ('x', 'String', Int(9)),
                          ('x', 'Guru', Int(8))]
                         )
                     ),
                ]
                )]
    assert parser.parse(program) == expected


def test_neg():
    program = """
    class A {
       funk():Type {
            case ~1 of
                x:Int => 10;
            esac
       };
    };"""
    expected = [Class('A', 'Object',
                [
                    Method('funk', [], 'Type',
                        Case(Neg(Int(1)),
                         [('x', 'Int', Int(10))]
                         )
                     ),
                ]
                )]
    assert parser.parse(program) == expected


def test_not():
    program = """
    class A {
       funk():Type {
            case not 1 of
                x:Int => 10;
            esac
       };
    };"""
    expected = [Class('A', 'Object',
                [
                    Method('funk', [], 'Type',
                        Case(Not(Int(1)),
                         [('x', 'Int', Int(10))]
                         )
                     ),
                ]
                )]
    assert parser.parse(program) == expected


def test_two_classes_defined():
    program = """
    class A {
       funk():Type {
            a
       };
    };
    class B {
       funk():Type {
            a
       };
    };
    """
    expected = [Class('A', 'Object',
                [
                    Method('funk', [], 'Type', Object('a')),
                ]
                ),
                Class('B', 'Object',
                [
                    Method('funk', [], 'Type', Object('a')),
                ]
                )]
    assert parser.parse(program) == expected


def test_operator_precedence_in_if_statements():
    program = """
    class A {
       funk():Type {
            if 3 + 4 < 0 then 1 else 2 fi
       };
    };"""
    expected = [Class('A', 'Object',
                [
                    Method('funk', [], 'Type',
                        If(Lt(Plus(Int(3), Int(4)), Int(0)), Int(1), Int(2))
                     ),
                ]
                )]
    assert parser.parse(program) == expected


