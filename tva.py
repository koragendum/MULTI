import threading

class Assignment:
    MUTATION = 0
    REVISION = 1
    PROPHECY = 2

    def __init__(self, left, right, kind):
        self.left = left
        self.right = right
        self.kind = kind

class Variable:
    def __init__(self, name, index):
        self.name = name
        self.index = index

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

    def eval(self, env):
        if not self.defined(env):
            return UNDEFINED
        if self.name not in env.var_histories:
            return None
        history = env.var_histories[self.name]
        if not self.index < len(history):
            return None
        return history[self.index].expression.eval(env)

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

    def eval(self, env):
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
            return left[right.value]
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

    def eval(self, env):
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
                assert operand.kind == 'tuple'
                return len(operand)
            case _:
                raise AssertionError(f'unknown operator "{self.operator}"')

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

    def eval(self, env):
        return self

class Undefined:
    def __init__(self):
        self.kind = 'undefined'

    def _str(self, parenthesize):
        return 'undefined'

    def __str__(self):
        return 'undefined'

    def __str__(self):
        return str(self.value)

    def __eq__(self, other):
        if isinstance(other, Undefined):
            raise AssertionError('...who knows?')
        return False

    def defined(self, env):
        return False

    def eval(self, env):
        return self

UNDEFINED = Undefined()

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

    def eval(self, env):
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

class CodeHistoryElement:
    def __init__(self):
        # varName: currentIndex
        self.var_history_indexes = {}
        self.prophecies = []
        self.pending_forks = []
        self.pending_dbgs = []

    def __str__(self):
        return f"CodeHistoryElem<\nVar History Indexes: {self.var_history_indexes},\nProphecies: {[str(proph) for proph in self.prophecies]},\nPending Forks: {self.pending_forks}>"

class VarHistoryElement:
    def __init__(self, expression, code_index):
        self.expression = expression
        self.code_index = code_index

    def __str__(self):
        return f"VarHistoryElem<Expression: {self.expression}, Code Index: {self.code_index}>"

class Environment:
    def __init__(self, var_count):
        # If idx = var_count[var] - 1, then var@idx is the last value of var.
        # The var_count dict is never mutated.
        self.var_histories = {}
        self.code_history = []
        self.var_count = var_count

    def fork(self, var_name, var_index, new_value):
        assert var_name in self.var_histories, "Reference to past event that never occurred."
        assert var_index < len(self.var_histories[var_name]), "Trying to fork to future event."
        code_index = self.var_histories[var_name][var_index].code_index
        assert code_index < len(self.code_history)

        new_env = Environment(self.var_count)
        new_env.code_history = self.code_history[:code_index + 1]
        code = self.code_history[code_index]
        new_env.var_histories = {
            var: history[:code.var_history_indexes[var] + 1] for var, history in self.var_histories.items() if var in code.var_history_indexes}
        old_var_history = new_env.var_histories[var_name][var_index]
        new_env.var_histories[var_name][var_index] = VarHistoryElement(new_value, old_var_history.code_index)
        return new_env, code_index

    def __str__(self):
        def str_var_histories(var_histories):
            return f"{{{",\n   ".join(f"{var}:\t[{",".join(str(elm) for elm in hist)}]" for var, hist in var_histories.items())}}}"
        return f"Environment:\n" + \
            f"Variable Histories:\n  {str_var_histories(self.var_histories)}\n" + \
            f"Code History:\n  [{",\n   ".join(str(elem) for elem in self.code_history)}]"

def run_code_to_completion(*args, output=True, **kwargs):
    threads = []
    try:
        run_code(*args, spawned_threads=threads, **kwargs)
    finally:
        for thread in threads:
            thread.join()

def run_code(code, env, universe_outputs, spawned_threads, start_index=0, universe="root", out_name="out", dbg_name="dbg"):
    spawn_count = 0
    def resolve_prophecies_and_pending_forks(prev_code, next_code):
        # Copy prophecies, but also try to resolve them.
        for prophecy in prev_code.prophecies:
            var, expression = prophecy
            prophecy_value = expression.eval(env)
            if prophecy_value is not None and var.name in env.var_histories and len(env.var_histories[var.name]) > var.index:
                future_value = env.var_histories[var.name][var.index].expression.eval(env)
                if future_value is not None:
                    assert future_value == prophecy_value, "Prophecy violated."
                    continue
            if next_code is not None:
                next_code.prophecies.append((var, prophecy_value or expression))

        # Check if any pending forks can be executed, or copy forward to try later.
        for fork in prev_code.pending_forks:
            fork_value = fork.right.eval(env)
            if fork_value is not None:
                new_env, code_index = env.fork(fork.left.name, fork.left.index, fork_value)
                args = (code, new_env, universe_outputs)
                kwargs = {"start_index": code_index+1, "universe": f"{universe}-{spawn_count}", "out_name": out_name, "dbg_name": dbg_name}
                thread = threading.Thread(target=run_code_to_completion, args=args, kwargs=kwargs)
                spawned_threads.append(thread)
                thread.start()
                spawn_count += 1
            elif next_code is not None:
                next_code.pending_forks.append(fork)

        # Print any pending debug statements that may have been resolved.
        #
        for dbg in prev_code.pending_dbgs:
            val = dbg[1].eval(env)
            if val is None:
                if next_code is not None:
                    next_code.pending_dbgs.append(dbg)
            else:
                print(f"dbg(u:{universe},l:{dbg[0]}): {str(val)}")

    for i, stmt in enumerate(code[start_index:]):
        next_code_history = CodeHistoryElement()

        # Important that pending forks and prophecies get resolved before
        # executing the stmt, otherwise a fork that breaks a prophecy would not
        # get caught.
        if len(env.code_history) != 0:
            resolve_prophecies_and_pending_forks(env.code_history[-1], next_code_history)

        match stmt.kind:
            case Assignment.MUTATION:
                assert stmt.left.index == 0 or \
                    (stmt.left.name in env.var_histories and len(env.var_histories[stmt.left.name]) == stmt.left.index), \
                    "Mutation to event in wrong timeline position."

                if stmt.left.name == dbg_name:
                    print(f"dbg(u:{universe},l:{i+start_index}): {str(stmt.right)}")
                    val = stmt.right.eval(env)
                    if val is None:
                        next_code_history.pending_dbgs.append((i+start_index, stmt.right))
                    else:
                        print(f"dbg(u:{universe},l:{i+start_index}): {str(val)}")

                if stmt.left.index == 0:
                    env.var_histories[stmt.left.name] = [VarHistoryElement(stmt.right.eval(env) or stmt.right, len(env.code_history))]
                else:
                    # Try to eval lhs. If it can't be evaluated then just take it as is.
                    env.var_histories[stmt.left.name].append(VarHistoryElement(stmt.right.eval(env) or stmt.right, i+start_index))
            case Assignment.REVISION:
                assert stmt.left.index >= 0, "Revision to event before big-bang."
                assert stmt.left.name in env.var_histories, "Revision to event that never occurred."
                assert stmt.left.index < len(env.var_histories[stmt.left.name]), "Revision to event in the future."

                fork_value = stmt.right.eval(env)
                if fork_value is None:
                    next_code_history.pending_forks.append(stmt)
                else:
                    new_env, code_index = env.fork(stmt.left.name, stmt.left.index, stmt.right.eval(env))
                    args = (code, new_env, universe_outputs)
                    kwargs = {"start_index": code_index+1, "universe": f"{universe}-{spawn_count}", "out_name": out_name, "dbg_name": dbg_name}
                    spawned_threads.append(threading.Thread(target=run_code_to_completion, args=args, kwargs=kwargs))
                    spawned_threads[-1].start()
                    spawn_count += 1
            case Assignment.PROPHECY:
                assert stmt.left.name not in env.var_histories or len(env.var_histories[stmt.left.name]) <= stmt.left.index, \
                    "Prophecy about event in the past."
                next_code_history.prophecies.append((stmt.left, stmt.right.eval(env) or stmt.right))
            case _:
                assert False, "Invalid stmt kind."

        # Now go and store all the current indexes
        for var in env.var_histories:
            next_code_history.var_history_indexes[var] = len(env.var_histories[var]) - 1
        env.code_history.append(next_code_history)

    # Try one more time to resolve prophecies and pending forks.
    if len(env.code_history) != 0:
        resolve_prophecies_and_pending_forks(env.code_history[-1], None)

    # TODO: if something in the output is indeterminate, fail this universe.
    if out_name in env.var_histories:
        outputs = [out.expression.eval(env) for out in env.var_histories[out_name]]
        if any(output is None for output in outputs):
            assert False, f"Indeterminate output, universe {universe} failed."
        universe_outputs[universe] = [str(out) for out in outputs]

# Do parsing, and lexing, generate a list of stmts, each stmt is an AST.
#
# x = 1
# x:+1 = 2
# x = 2
# x:0 = 3
code = [
    Assignment(Variable("x", 0), Literal(1, 'int'), Assignment.MUTATION),
    Assignment(Variable("x", 1), Literal(2, 'int'), Assignment.PROPHECY),
    Assignment(Variable("x", 1), Literal(2, 'int'), Assignment.MUTATION),
    Assignment(Variable("x", 1), Literal(3, 'int'), Assignment.REVISION)]
# run_code(code, Environment())

# x = 1
# x:+1 = y:+1
# z = 2
# x = 2
# y = z
# z:0 = 3
code = [
    Assignment(Variable("x", 0), Literal(1, 'int'), Assignment.MUTATION),
    Assignment(Variable("x", 1), Variable("y", 0), Assignment.PROPHECY),
    Assignment(Variable("dbg", 0), Literal(1, 'int'), Assignment.MUTATION),
    Assignment(Variable("dbg", 0), Variable("y", 0), Assignment.MUTATION),
    Assignment(Variable("dbg", 0), Variable("x", 0), Assignment.MUTATION),
    Assignment(Variable("z", 0), Literal(2, 'int'), Assignment.MUTATION),
    Assignment(Variable("dbg", 0), Variable("y", 0), Assignment.MUTATION),
    Assignment(Variable("x", 1), Literal(2, 'int'), Assignment.MUTATION),
    Assignment(Variable("y", 0), Variable("z", 0), Assignment.MUTATION),
    Assignment(Variable("z", 0), Literal(3, 'int'), Assignment.REVISION),
    Assignment(Variable("out", 0), Variable("z", 0), Assignment.MUTATION)
]
output={}
var_count = {'x': 2, 'y': 1, 'z': 1, 'out': 1, 'dbg': 1}
run_code_to_completion(code, Environment(var_count), output)
for _, outputs in output.items():
    for out in outputs:
        print(out)
