import threading

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

class CodeHistoryElement:
    def __init__(self):
        # varName: currentIndex
        self.var_history_indexes = {}
        self.prophecies = []
        self.pending_forks = []

class VarHistoryElement:
    def __init__(self, expression, code_index):
        self.expression = expression
        self.code_index = code_index

class Environment:
    def __init__(self):
        self.var_histories = {}
        self.code_history = []

    def fork(self, var_name, var_index, new_value):
        assert var_name in self.var_histories, "Reference to past event that never occurred."
        assert var_index < len(self.var_histories[var_name]), "Trying to fork to future event."
        code_index = self.var_histories[var_name][var_index].code_index
        assert code_index < len(self.code_history)

        new_env = Environment()
        new_env.code_history = env.code_history[:code_index + 1]
        new_env.var_histories = {var: history[:new_env.code_history.var_history_indexes[var] + 1] for var, history in env.var_histories.items()}
        new_env.var_histories[var_name][var_index].expression = new_value
        return new_env, code_index

def run_code(code, start_index=0, env=Environment()):
    for stmt in code[start_index:]:
        next_code_history = CodeHistoryElement()
        match stmt.kind:
            case Assignment.MUTATION:
                assert stmt.left.index == 0 or \
                    (stmt.left.name in env.var_histories and len(env.var_histories[stmt.left.name]) == stmt.left.index), \
                    "Mutation to event in wrong timeline position."
                
                # Try to eval lhs. If it can't be evaluated then just take it as is.
                env.var_histories[stmt.left.name].append(stmt.left.eval(env) or stmt.left)
            case Assignment.REVISION:
                assert stmt.left.index >= 0, "Revision to event before big-bang."
                assert stmt.left.name in env.var_histories, "Revision to event that never occurred."
                assert stmt.left.index < len(env.var_histories[stmt.left.name]), "Revision to event in the future."

                fork_value = stmt.right.eval(env)
                if fork_value is None:
                    next_code_history.pending_forks.append(stmt)
                else:
                    new_env, code_index = env.fork(stmt.left.name, stmt.left.index, stmt.right.eval(env))
                    threading.Thread(target=run_code, args=(code, code_index, new_env)).start()
            case Assignment.PROPHECY:
                assert stmt.left.name not in env.var_histories or len(env.var_histories[stmt.left.name]) <= stmt.left.index, \
                    "Prophecy about event in the past."
                next_code_history.prophecies.append((stmt.left, stmt.right.eval(env) or stmt))
            case _:
                assert False, "Invalid stmt kind."

        # Copy prophecies, but also try to resolve them.
        for prophecy in env.code_history.prophecies:
            var, expression = prophecy
            prophecy_value = expression.eval(env)
            if prophecy_value is not None and var.name in env.var_histories and len(env.var_histories[var.name]) > var.index:
                future_value = env.var_histories[var.name][var.index].expression.eval(env)
                if future_value is not None:
                    assert future_value == prophecy_value, "Prophecy violated."
                    continue
            next_code_history.prophecies.append((var, prophecy_value or expression))
        
        # Check if any pending forks can be executed.
        for fork in env.code_history.pending_forks:
            fork_value = fork.right.eval(env)
            if fork_value is not None:
                new_env, code_index = env.fork(fork.left.name, fork.left.index, fork_value)
                threading.Thread(target=run_code, args=(code, code_index, new_env)).start()
            else:
                next_code_history.pending_forks.append(fork)

# Do parsing, and lexing, generate a list of stmts, each stmt is an AST.
#
code = []
env = Environment()
run_code(code)