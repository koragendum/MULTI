class Variable:
    def __init__(self, name, index, offset=None):
        self.name = name
        self.index = index
        self.offset = offset

    def _str(self, parenthesize):
        return f'{self.name}@{self.index}'

    def __str__(self):
        return self._str(False)

    def defined(self, env):
        if self.name not in env.var_count:
            raise AssertionError()
        if self.index < 0:
            return False
        if not self.index < env.var_count[self.name]:
            return False
        return True

    def eval(self, env, visited=None):
        visited = visited or set()
        if self.name in visited:
            return None
        visited.add(self.name)
        if not self.defined(env):
            return UNDEFINED
        if self.name not in env.var_histories:
            return None
        history = env.var_histories[self.name]
        if not self.index < len(history):
            return None
        return history[self.index].expression.eval(env, visited)

class Undefined:
    def __init__(self):
        self.kind = 'undefined'

    def _str(self, parenthesize):
        return 'undefined'

    def __str__(self):
        return 'undefined'

    def __eq__(self, other):
        return True
        if isinstance(other, Undefined):
            raise AssertionError('...who knows?')
        return False

    def defined(self, env):
        return False

    def eval(self, env, visited=None):
        return self

UNDEFINED = Undefined()

class Literal:
    def __init__(self, value, kind):
        self.value = value
        self.kind = kind

    def _str(self, parenthesize):
        match self.kind:
            case "atom":
                return f'“{self.value}”'
            case "bool":
                return 'true' if self.value else 'false'
            case "int":
                return str(self.value)
            case _:
                raise AssertionError()

    def __str__(self):
        return self._str(False)

    def __eq__(self, other):
        return isinstance(other, Literal) and self.value == other.value

    def defined(self, env):
        return True

    def eval(self, env, visited=None):
        return self

class Tuple:
    def __init__(self, elements, concrete=False):
        self.elements = elements
        self.kind = 'tuple'
        self.concrete = concrete

    def _str(self, parenthesize):
        inner = ", ".join(elem._str(False) for elem in self.elements)
        return f'[{inner}]'

    def __str__(self):
        return self._str(False)

    def __len__(self):
        return len(self.elements)

    def __eq__(self, other):
        if not isinstance(other, Tuple):
            return False
        assert self.concrete
        assert other.concrete
        return other.elements == self.elements

    def defined(self, env):
        return all(elem.defined(env) for elem in self.elements)

    def eval(self, env, visited=None):
        if self.concrete:
            return self
        values = []
        for elem in self.elements:
            value = elem.eval(env)
            if value is None:
                return None
            if value.kind == 'undefined':
                return UNDEFINED
            values.append(value)
        return Tuple(values, concrete=True)

class UnaryExpression:
    def __init__(self, operand, operator):
        self.operand = operand
        self.operator = operator

    def _str(self, parenthesize):
        opd = self.operand._str(True)
        if parenthesize:
            return f'({self.operator} {opd})'
        return f'{self.operator} {opd}'

    def __str__(self):
        return self._str(False)

    def defined(self, env):
        return self.operand.defined(env)

    def eval(self, env, visited=None):
        if self.operator == "def":
            return Literal(self.operand.defined(env), 'bool')
        operand = self.operand.eval(env)
        if operand is None:
            return None
        if operand.kind == 'undefined':
            return UNDEFINED
        match self.operator:
            case "neg":
                assert operand.kind == 'int'
                return Literal(-operand.value, 'int')
            case "not":
                assert operand.kind == 'bool'
                return Literal(not operand.value, 'bool')
            case "len":
                if operand.kind == 'tuple':
                    return Literal(len(operand.elements), 'int')
                if operand.kind == 'atom':
                    return Literal(len(operand.value), 'int')
                raise AssertionError()
            case _:
                raise AssertionError(f'unknown operator "{self.operator}"')

class BinaryExpression:
    def __init__(self, left, right, operator):
        self.left = left
        self.right = right
        self.operator = operator

    def _str(self, parenthesize):
        lhs = self.left._str(True)
        rhs = self.right._str(True)
        if parenthesize:
            return f'({lhs} {self.operator} {rhs})'
        return f'{lhs} {self.operator} {rhs}'

    def __str__(self):
        return self._str(False)

    def defined(self, env):
        return self.left.defined(env) and self.right.defined(env)

    def eval(self, env, visited=None):
        left = self.left.eval(env)
        right = self.right.eval(env)
        if left is None or right is None:
            return None
        if left.kind == 'undefined' or right.kind == 'undefined':
            return UNDEFINED
        if self.operator == 'idx':
            assert left.kind == 'tuple' and right.kind == 'int'
            if right.value < 0 or not right.value < len(left):
                return UNDEFINED
            return left.elements[right.value]
        assert left.kind == right.kind
        kind = left.kind
        match self.operator:
            case "add":
                if kind == 'int':
                    return Literal(left.value + right.value, 'int')
                elif kind == 'tuple':
                    return Tuple(left.elements + right.elements)
                elif kind == 'atom':
                    return Literal(left.value + right.value, 'atom')
                else:
                    raise AssertionError()
            case "sub":
                assert kind == 'int'
                return Literal(left.value - right.value, 'int')
            case "mul":
                assert kind == 'int'
                return Literal(left.value * right.value, 'int')
            case "div":
                assert kind == 'int'
                return Literal(left.value // right.value, 'int')
            case "mod":
                assert kind == 'int'
                return Literal(left.value % right.value, 'int')
            case "and":
                if kind == 'bool':
                    return Literal(left.value and right.value, 'bool')
                elif kind == 'int':
                    return Literal(min(left.value, right.value), 'int')
                else:
                    raise AssertionError()
            case "or":
                if kind == 'bool':
                    return Literal(left.value or right.value, 'bool')
                elif kind == 'int':
                    return Literal(max(left.value, right.value), 'int')
                else:
                    raise AssertionError()
            case "gt":
                assert kind == 'int'
                return Literal(left.value > right.value, 'bool')
            case "lt":
                assert kind == 'int'
                return Literal(left.value < right.value, 'bool')
            case "geq":
                assert kind == 'int'
                return Literal(left.value >= right.value, 'bool')
            case "leq":
                assert kind == 'int'
                return Literal(left.value <= right.value, 'bool')
            case "eq":
                return Literal(left == right, 'bool')
            case "neq":
                return Literal(left != right, 'bool')
            case _:
                return None

class Assignment:
    MUTATION = 0
    REVISION = 1
    PROPHECY = 2

    def __init__(self, left, right, kind, line=None):
        self.left = left
        self.right = right
        self.kind = kind
        self.line = line

    def _str(self, parenthesize):
        num = f'{self.line}: ' if self.line is not None else ''
        knd = {
            Assignment.MUTATION: 'mut',
            Assignment.REVISION: 'rev',
            Assignment.PROPHECY: 'pro',
        }[self.kind]
        lhs = self.left._str(False)
        rhs = self.right._str(False)
        if parenthesize:
            return f'({num}{knd} {lhs} = {rhs})'
        return f'{num}{knd} {lhs} = {rhs}'

    def __str__(self):
        return self._str(False)
