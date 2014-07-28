from compiler.parser import parser


def test_empty_class_definition():
    program = "class A { };"
    expected = ('class', 'A', 'Object', [])
    assert parser.parse(program) == expected


def test_class_definition_with_inherits():
    program = "class A inherits Top { };"
    expected = ('class', 'A', 'Top', [])
    assert parser.parse(program) == expected


def test_class_with_uninitialized_attributes():
    program = """
    class A {
        attr1:AttrType;
        attr2: AttrType;
    };"""
    expected = ('class', 'A', 'Object',
                [
                    ('attr', 'attr1', 'AttrType', None),
                    ('attr', 'attr2', 'AttrType', None),
                ]
                )
    assert parser.parse(program) == expected


def test_class_with_initialized_attributes():
    program = """
    class A {
        attr1:AttrType <- otherObj;
        attr2: AttrType <- initialObj;
    };"""
    expected = ('class', 'A', 'Object',
                [
                    ('attr', 'attr1', 'AttrType', ('object', 'otherObj')),
                    ('attr', 'attr2', 'AttrType', ('object', 'initialObj')),
                ]
                )
    assert parser.parse(program) == expected


def test_class_with_method_without_formals():
    program = """class A { funk():ReturnType { returnvalue }; };"""
    expected = ('class', 'A', 'Object',
                [
                    ('method', 'funk', [], 'ReturnType', ('object', 'returnvalue')),
                ]
                )
    assert parser.parse(program) == expected


def test_class_with_method_with_formals():
    program = """class A { funk(x:X, y:Y):ReturnType { x }; };"""
    expected = ('class', 'A', 'Object',
                [
                    ('method', 'funk', [('x', 'X'), ('y', 'Y')], 'ReturnType', ('object', 'x')),
                ]
                )
    assert parser.parse(program) == expected


def test_class_with_method_returning_int():
    program = """class A { funk():ReturnType { 12 }; };"""
    expected = ('class', 'A', 'Object',
                [
                    ('method', 'funk', [], 'ReturnType', ('int', 12)),
                ]
                )
    assert parser.parse(program) == expected


def test_class_with_method_returning_str():
    program = """class A { funk():ReturnType { "blabla" }; };"""
    expected = ('class', 'A', 'Object',
                [
                    ('method', 'funk', [], 'ReturnType', ('str', 'blabla')),
                ]
                )
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
    expected = ('class', 'A', 'WithVar',
                [
                    ('method', 'set_var', [('num', 'Int')], 'SELF_TYPE', ('block', [('object', 'self')])),
                ]
                )
    assert parser.parse(program) == expected


def test_simple_dispatch_with_no_args():
    program = """
    class A {
       funk():Type {
            obj.method()
       };
    };"""
    expected = ('class', 'A', 'Object',
                [
                    ('method', 'funk', [], 'Type', ('dispatch', ('object', 'obj'), 'method', [])),
                ]
                )
    assert parser.parse(program) == expected


def test_simple_dispatch_with_one_arg():
    program = """
    class A {
       funk():Type {
            obj.method(2)
       };
    };"""
    expected = ('class', 'A', 'Object',
                [
                    ('method', 'funk', [], 'Type', ('dispatch', ('object', 'obj'), 'method', [('int', 2)])),
                ]
                )
    assert parser.parse(program) == expected


def test_simple_dispatch_with_multiple_args():
    program = """
    class A {
       funk():Type {
            obj.method(2, "blabla", x)
       };
    };"""
    expected = ('class', 'A', 'Object',
                [
                    ('method', 'funk', [], 'Type', ('dispatch', ('object', 'obj'), 'method', [('int', 2), ('str', 'blabla'), ('object', 'x')])),
                ]
                )
    assert parser.parse(program) == expected


def test_static_dispatch_with_no_args():
    program = """
    class A {
       funk():Type {
            obj@Klass.method()
       };
    };"""
    expected = ('class', 'A', 'Object',
                [
                    ('method', 'funk', [], 'Type', ('static_dispatch', ('object', 'obj'), 'Klass', 'method', [])),
                ]
                )
    assert parser.parse(program) == expected


def test_self_dispatch_with_no_args():
    program = """
    class A {
       funk():Type {
            method()
       };
    };"""
    expected = ('class', 'A', 'Object',
                [
                    ('method', 'funk', [], 'Type', ('self_dispatch', 'method', [])),
                ]
                )
    assert parser.parse(program) == expected


def test_if_statements():
    program = """
    class A {
       funk():Type {
            if x < 0 then 1 else 2 fi
       };
    };"""
    expected = ('class', 'A', 'Object',
                [
                    ('method', 'funk', [], 'Type',
                        ('if', ('<', ('object', 'x'), ('int', 0)), ('int', 1), ('int', 2))
                     ),
                ]
                )
    assert parser.parse(program) == expected


def test_while_statements():
    program = """
    class A {
       funk():Type {
            while x < 0 loop 1 pool
       };
    };"""
    expected = ('class', 'A', 'Object',
                [
                    ('method', 'funk', [], 'Type',
                        ('while', ('<', ('object', 'x'), ('int', 0)), ('int', 1))
                     ),
                ]
                )
    assert parser.parse(program) == expected


def test_let_statement():
    program = """
    class A {
       funk():Type {
            let x:TypeX in x + 1
       };
    };"""
    expected = ('class', 'A', 'Object',
                [
                    ('method', 'funk', [], 'Type',
                        ('let', 'x', 'TypeX', None, ('+', ('object', 'x'), ('int', 1)))
                     ),
                ]
                )
    assert parser.parse(program) == expected


def test_let_statement_with_assignment():
    program = """
    class A {
       funk():Type {
            let x:TypeX <- 5 in x + 1
       };
    };"""
    expected = ('class', 'A', 'Object',
                [
                    ('method', 'funk', [], 'Type',
                        ('let', 'x', 'TypeX', ('int', 5), ('+', ('object', 'x'), ('int', 1)))
                     ),
                ]
                )
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
    expected = ('class', 'A', 'Object',
                [
                    ('method', 'funk', [], 'Type',
                        ('let', 'x', 'TypeX', ('int', 5),
                            ('let', 'y', 'TypeY', None,
                                ('+', ('object', 'x'), ('int', 1))
                             )
                        )
                     ),
                ]
                )
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
    expected = ('class', 'A', 'Object',
                [
                    ('method', 'funk', [], 'Type',
                        ('let', 'x', 'TypeX', None,
                            ('let', 'y', 'TypeY', ('int', 3),
                                ('let', 'z', 'ZType', ('*', ('+', ('int', 2), ('int', 2)), ('int', 5)),
                                    ('+', ('object', 'x'), ('int', 1))
                                )
                            )
                        )
                     ),
                ]
                )
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
    expected = ('class', 'A', 'Object',
                [
                    ('method', 'funk', [], 'Type',
                        ('let', 'x', 'TypeX', ('int', 5),
                                ('+', ('object', 'x'), ('int', 1))
                        )
                     ),
                ]
                )
    assert parser.parse(program) == expected


# do CASE


def test_new():
    program = """
    class A {
       funk():Type {
            new B
       };
    };"""
    expected = ('class', 'A', 'Object',
                [
                    ('method', 'funk', [], 'Type',
                        ('new', 'B')
                     ),
                ]
                )
    assert parser.parse(program) == expected


def test_isvoid():
    program = """
    class A {
       funk():Type {
            isvoid B
       };
    };"""
    expected = ('class', 'A', 'Object',
                [
                    ('method', 'funk', [], 'Type',
                        ('isvoid', 'B')
                     ),
                ]
                )
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
    expected = ('class', 'A', 'Object',
                [
                    ('method', 'funk', [], 'Type',
                        ('case', ('int', 1),
                         [('x', 'Int', ('int', 10)),
                          ('x', 'String', ('int', 9)),
                          ('x', 'Guru', ('int', 8))]
                         )
                     ),
                ]
                )
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
    expected = ('class', 'A', 'Object',
                [
                    ('method', 'funk', [], 'Type',
                        ('case', ('neg', ('int', 1)),
                         [('x', 'Int', ('int', 10))]
                         )
                     ),
                ]
                )
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
    expected = ('class', 'A', 'Object',
                [
                    ('method', 'funk', [], 'Type',
                        ('case', ('not', ('int', 1)),
                         [('x', 'Int', ('int', 10))]
                         )
                     ),
                ]
                )
    assert parser.parse(program) == expected


