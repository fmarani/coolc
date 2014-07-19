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


