from lexer import *
from objects import *

# Arranged from high to low precedence. Unary operators are 'prefix'
#   or 'postfix', and binary operators are 'left' or 'right' associative.

# The None operator is function application.

OPERATORS = [
    ('left',   ['idx'                                ]),
    ('prefix', ['add', 'sub', 'not', 'len', 'def'    ]),
    ('left',   ['mul', 'div', 'mod'                  ]),
    ('left',   ['add', 'sub'                         ]),
    ('left',   ['eq', 'neq', 'geq', 'leq', 'gt', 'lt']),
    ('left',   ['and'                                ]),
    ('left',   ['or'                                 ]),
    ('right',  ['sepr'                               ]),
]

class ParseTree:
    def __init__(self, root, children):
        self.root = root
        self.children = children
        self.kind = 'tree'

    def __str__(self):
        tr = "\x1B[38;5;129mTree\x1B[39m"
        return f"{tr} of {self.root}"

    def __len__(self):
        return len(self.children)

    def __iter__(self):
        return iter(self.children)

    def __getitem__(self, x):
        return self.children[x]

    def left(self):
        return self.children[0]

    def right(self):
        return self.children[-1]

    def extract(self):
        return sum((x.extract() for x in self.children), [])

    def show(self, top=True):
        lines = [str(self)]
        num_children = len(self.children)
        for idx, child in enumerate(self.children):
            last = (idx + 1 == num_children)
            mark = "\u2514" if last else "\u251C"
            mark = f"\x1B[2m{mark}\u2500\x1B[22m "
            if isinstance(child, Token):
                lines.append(mark + str(child))
            else:
                block = child.show(top=False)
                lines.append(mark + block[0])
                margin = "   " if last else "\x1B[2m\u2502\x1B[22m  "
                for ln in block[1:]:
                    lines.append(margin + ln)
        if top: print("\n".join(lines))
        return lines

#~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~

prefix_ops  = {}    # {str -> precedence : int}
postfix_ops = {}    # {str -> precedence : int}
binary_ops  = {}    # {str -> (precedence : int, right-assoc : bool)}

LEVELS = len(OPERATORS)

for idx, (fixity, operators) in enumerate(OPERATORS):
    prec = LEVELS - 1 - idx

    if fixity in ('prefix', 'postfix'):
        op_dict = (postfix_ops if fixity == 'postfix' else prefix_ops)
        for op in operators:
            if op is None:
                raise AssertionError("application must be a binary operator")
            op_dict[op] = prec

    elif fixity in ('left', 'right'):
        rassoc = (fixity == 'right')
        for op in operators:
            binary_ops[op] = (prec, rassoc)
    else:
        raise AssertionError("associativity should be 'left', 'right', 'prefix', or 'postfix'")

#~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~

def _parse_operators(seq, min_precedence):
    """
    Returns a token, ParseTree, ParseFailure, or None.
    """
    if len(seq) == 0:
        return None

    lhs = seq[0]
    index = 1
    if isinstance(lhs, Token) and lhs.kind == 'symbol':
        if lhs.value in prefix_ops:
            precedence = prefix_ops[lhs.value]
            rhs_parse = _parse_operators(seq[index:], precedence)
            if rhs_parse is None:
                return ParseFailure('unary operator missing argument', lhs)
            if isinstance(rhs_parse, ParseFailure):
                return rhs_parse
            rhs, num_tokens = rhs_parse
            index += num_tokens
            lhs = ParseTree(lhs, [rhs])

        elif lhs.value in binary_ops:
            return ParseFailure('binary operator missing lefthand argument', lhs)

    while True:
        if not index < len(seq):
            break

        op = seq[index]
        is_symbol = isinstance(op, Token) and op.kind == 'symbol'
        if is_symbol and op.value in postfix_ops:
            precedence = postfix_ops[op.value]
            if precedence < min_precedence:
                break
            lhs = ParseTree(op, [lhs])
            index += 1
            continue

        elif is_symbol and op.value in binary_ops:
            precedence, rassoc = binary_ops[op.value]
            if precedence < min_precedence:
                break
            index += 1
            if not index < len(seq):
                return ParseFailure('binary operator missing righthand argument', op)

        else:
            return ParseFailure('missing operator', seq[index])
            # precedence, rassoc = binary_ops[None]
            # if precedence < min_precedence:
            #     break

        rhs_parse = _parse_operators(seq[index:], precedence + (0 if rassoc else 1))
        if rhs_parse is None:
            raise AssertionError()
        if isinstance(rhs_parse, ParseFailure):
            return rhs_parse
        rhs, num_tokens = rhs_parse

        index += num_tokens
        if is_symbol and op.value == 'sepr':
            rightl = rhs.children if (rhs.kind == 'tree' and rhs.root == 'list') else [rhs]
            lhs = ParseTree('list', [lhs] + rightl)
        else:
            lhs = ParseTree(op, [lhs, rhs])

    return (lhs, index)

def parse_operators(seq):
    parse = _parse_operators(seq, 0)
    if parse is None:
        raise AssertionError()
    if isinstance(parse, ParseFailure):
        return parse
    parse, _ = parse
    return parse

def parse_interior(container, seq):
    """
    container -- the context in which seq appears ('root', 'parens', or 'brackets')
    seq       -- a list of tokens and/or ParseTrees guaranteed to not include any delimiters
    """
    if len(seq) == 0:
        return None
    op_parse = parse_operators(seq)
    if op_parse is None:
        raise AssertionError()
    if isinstance(op_parse, ParseFailure):
        return op_parse
    if container == 'brackets':
        return ParseTree(container, [op_parse])
    return op_parse

DELIMITERS = {'pL', 'pR', 'bL', 'bR'}
LEFTDELIMS = {'pL': 'pR', 'bL': 'bR'}
DELIMNAMES = {
    'pR': 'parens',
    'bR': 'brackets',
}

def parse_expression(stream):
    stack = []
    seq = []
    index = 0
    while True:
        token = next(stream)
        if token is None:
            break
        if isinstance(token, ParseFailure):
            return token
        if token.kind == 'newline':
            if len(stack) == 0:
                break
            else:
                continue

        seq.append(token)

        if token.kind != 'symbol' or token.value not in DELIMITERS:
            index += 1
            continue

        if token.value in LEFTDELIMS:
            stack.append((index, LEFTDELIMS[token.value]))
            index += 1
            continue

        if len(stack) == 0:
            return ParseFailure('unpaired delimiter', token)

        left_index, expected_delim = stack[-1]
        if token.value != expected_delim:
            return ParseFailure('mismatched or unpaired delimiter', token)

        interior = seq[left_index+1:index]
        inter_length = len(interior)

        container = DELIMNAMES[token.value]
        replacement = parse_interior(container, interior)
        if replacement is None:
            if container == 'brackets':
                replacement = ParseTree(container, [])
            else:
                return ParseFailure('empty region', (seq[left_index], token))
        if isinstance(replacement, ParseFailure):
            return replacement
        repl_length = 1

        seq = seq[:left_index] + [replacement] + seq[index+1:]
        index = index - 1 - (inter_length - repl_length) - 1

        stack.pop()
        index += 1

    if len(stack) > 0:
        left_index, _ = stack[-1]
        return ParseFailure('unpaired delimiter', seq[left_index])

    # Parse the delimiter-free sequence
    return parse_interior('root', seq)

def parse_statement(stream):
    while True:
        token = next(stream)
        if token is None:
            return None
        if isinstance(token, ParseFailure):
            return token
        if token.kind != 'newline':
            break

    note = None

    if token.kind == 'variable':
        assn = next(stream)
        if assn is None:
            failure = token

        elif isinstance(assn, ParseFailure):
            return assn

        elif assn.kind == 'symbol' and assn.text == '=':
            expr = parse_expression(stream)
            if expr is None:
                failure = assn
                note = "missing expression"
            elif isinstance(expr, ParseFailure):
                return expr
            else:
                return ParseTree(assn, [token, expr])

        else:
            failure = assn

    elif token.kind == 'keyword':
        if token.value == 'assert':
            expr = parse_expression(stream)
            if expr is None:
                failure = token
                note = "missing expression"
            elif isinstance(expr, ParseFailure):
                return expr
            else:
                return ParseTree(token, [expr])

        elif token.value == 'die':
            return ParseTree(token, [])

        else:
            failure = token

    else:
        failure = token

    if note is None:
        i = lambda s: f'\x1B[3m{s}\x1B[23m'
        note = f'statements must be “{i("variable")} = {i("expression")}”,' \
                f' “assert {i("expression")}”, or “die”'
    return ParseFailure('invalid statement', failure, note)

def _reify(expr):
    if expr.kind == 'keyword':
        if expr.value == 'true':
            return Literal(True, 'bool')

        elif expr.value == 'false':
            return Literal(False, 'bool')

        else:
            return ParseFailure('keyword only valid at head of statement', expr)

    elif expr.kind == 'variable':
        name, offset = expr.value
        return Variable(name, None, offset)

    elif expr.kind == 'number':
        return Literal(expr.value, 'int')

    elif expr.kind == 'atom':
        return Literal(expr.value, 'atom')

    elif expr.kind == 'symbol':
        raise AssertionError()

    elif expr.kind == 'tree':
        if expr.root == 'brackets':
            if len(expr) == 0:
                return Tuple([])

            assert len(expr) == 1
            child = expr.left()
            if child.kind == 'tree' and child.root == 'list':
                reified = []
                for item in child:
                    inner = _reify(item)
                    if isinstance(inner, ParseFailure):
                        return inner
                    reified.append(inner)
                return Tuple(reified)

            else:
                inner = _reify(child)
                if isinstance(inner, ParseFailure):
                    return inner
                return Tuple([inner])

        if expr.root == 'list':
            return ParseFailure('item lists must be bracketed', expr)

        assert expr.root.kind == 'symbol'

        match expr.root.value:
            # polyadic
            case 'add' | 'sub':
                if len(expr) == 1:
                    inner = _reify(expr.left())
                    if isinstance(inner, ParseFailure):
                        return inner
                    return UnaryExpression(inner, expr.root.value)

                if len(expr) == 2:
                    lhs = _reify(expr.left())
                    if isinstance(lhs, ParseFailure):
                        return lhs
                    rhs = _reify(expr.right())
                    if isinstance(rhs, ParseFailure):
                        return rhs
                    return BinaryExpression(lhs, rhs, expr.root.value)

                raise AssertionError()

            # unary
            case 'not' | 'len' | 'def':
                assert len(expr) == 1
                inner = _reify(expr.left())
                if isinstance(inner, ParseFailure):
                    return inner
                return UnaryExpression(inner, expr.root.value)

            # binary
            case 'idx' | 'mul' | 'div' | 'mod' \
                | 'eq' | 'neq' | 'geq' | 'leq' | 'gt' | 'lt' \
                | 'and' | 'or':
                assert len(expr) == 2
                lhs = _reify(expr.left())
                if isinstance(lhs, ParseFailure):
                    return lhs
                rhs = _reify(expr.right())
                if isinstance(rhs, ParseFailure):
                    return rhs
                return BinaryExpression(lhs, rhs, expr.root.value)

            case _:
                raise AssertionError()

    else:
        raise AssertionError()

def reify(statement):
    # returns ParseFailure or (Assignment, line number)

    if statement.root.kind == 'keyword':
        if statement.root.value == 'die':
            raise NotImplementedError() # TODO

        if statement.root.value == 'assert':
            raise NotImplementedError() # TODO

        raise AssertionError()

    assert statement.root.kind == 'symbol'
    assert statement.root.text == '='
    assert statement.left().kind == 'variable'

    name, offset = statement.left().value
    lefthand = Variable(name, None, offset)

    righthand = _reify(statement.right())
    if isinstance(righthand, ParseFailure):
        return righthand

    if offset is None:
        kind = Assignment.MUTATION
    else:
        kind = Assignment.PROPHECY if offset > 0 else Assignment.REVISION

    return Assignment(lefthand, righthand, kind, statement.left().line)

def _reindex(obj, count):
    if isinstance(obj, Variable):
        if obj.name not in count:
            count[obj.name] = -1
        obj.index = count[obj.name] + (0 if obj.offset is None else obj.offset)
    if isinstance(obj, Tuple):
        for elem in obj.elements:
            _reindex(elem, count)
    if isinstance(obj, UnaryExpression):
        _reindex(obj.operand, count)
    if isinstance(obj, BinaryExpression):
        _reindex(obj.left, count)
        _reindex(obj.right, count)

def reindex(statements):
    count = {}
    for assn in statements:
        if not isinstance(assn, Assignment):
            raise NotImplementedError()

        _reindex(assn.right, count)

        if assn.kind == Assignment.MUTATION:
            x = count.get(assn.left.name, -1) + 1
            assn.left.index = x
            count[assn.left.name] = x

        if assn.kind == Assignment.REVISION:
            assn.left.index = count.get(assn.left.name, -1) + assn.left.offset

        if assn.kind == Assignment.PROPHECY:
            assn.left.index = count.get(assn.left.name, -1) + assn.left.offset

    for name in count:
        count[name] += 1

    return count

#~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~

if __name__ == '__main__':

    def prompt():
        print("\x1B[2mparse:\x1B[22m", end=' ')
        line = input()
        if line in ['exit', 'quit']:
            exit()
        return line + "\n"

    stream = TokenStream("", prompt)
    statements = []

    while True:
        result = parse_statement(stream)
        if result is None:
            pass
        elif isinstance(result, ParseFailure):
            result.show(stream.log())
            stream.clear_line()
        else:
            result.show()
            reified = reify(result)
            if isinstance(reified, ParseFailure):
                reified.show(stream.log())
            else:
                statements.append(reified)
                count = reindex(statements)
                print(reified)
                print(count)
