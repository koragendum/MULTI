# Do parsing, and lexing, generate a list of stmts, each stmt is an AST.
#
code = []

# X = K
class Assignment:
    MUTATION = 0
    REVISION = 1
    PROPHECY = 2

    def __init__(self):
        self.left = None
        self.right = None
        self.kind = Assignment.MUTATION

# X or X:N
class Variable:
    def __init__(self, name, index):
        self.name = name

        # Indexes are ints. These should be absolute coming from parser.
        self.index = index

    # Should return either a Literal if it's evaluable, or return None if it isn't.
    def eval(self, env):
        pass

# Note: code history needs to keep track of unresolved prophecies at each point
# so that forks that violate prophecies immediately die.

# + - * / % and or < > == != <= >= . (tuple indexing)
class BinaryOperator:
    def __init__(self, left, right, operator):
        self.left = left
        self.right = right
        self.operator = operator

    def eval(self, env):
        pass

# - + not
class UnaryOperator:
    def __init__(self, operand, operator):
        self.operand = operand

# Undefined / Boolean / Character / Integer
class Literal:
    def __init__(self, value):
        self.value = value

    def eval(self, env):
        return self.value

class Tuple:
    def __init__(self, values):
        self.values = values

    def eval(self, env):
        return [value.eval(env) for value in self.values]

env = {
    'x': HistoryOfX,
}

History = {
    index: (Expression, codeIndex),
    ...
}