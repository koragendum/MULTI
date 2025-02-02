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

class ConcreteValue:
    def is_thunk(self):
        return False

    def get_value(self):
        return self.value

# Holds a representation of an expression, and eval returns one of:
# - A concrete value if all thinks are known.
# - None if we're waiting for some other thunks to resolve.
#
class ThunkValue:    
    def is_prophecy(self):
        return False

    def is_thunk(self):
        return True

    def eval(self, env):
        pass

class ProphesizedValue:
    def is_thunk(self):

class ExecutionFailure(Exception):
    def __init__(self, message):
        super().__init__(message)

# Used to represent a value of an object - may either be a concrete value or some future unknown or expression based on future unknowns.
class ObjValue:
    pass

class Obj:
    def __init__(self, name):
        self.name = name
        self.current_time = -1
        self.values = {}

    def get(self, delta_time):
        pass

# x@N if just x, then it's equivalent to x@0
class AliasAtDeltaTime:
    def eval(self, env):
        self.delta_time = self.right.eval(env)


# No `eval` on assignment as this gets evaluated by the runner to more easily enable time travel.
class Assignment:
    pass

env = {}
for stmt in code:
