from lexer import *

# Arranged from high to low precedence. Unary operators are 'prefix'
#   or 'postfix', and binary operators are 'left' or 'right' associative.

# The None operator is function application.

OPERATORS = [
    ('left',   ['idx'                                ]),
    ('prefix', ['add', 'sub', 'not', 'len', 'def'    ]),
    ('left',   ['mul', 'div', 'mod'                  ]),
    ('left',   ['add', 'sub'                         ]),
    ('left',   ['eq', 'neq', 'geq', 'leq', 'gt', 'lt']),
    ('left',   ['sepr'                               ]),
]

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
            precedence, rassoc = binary_ops[None]
            if precedence < min_precedence:
                break

        rhs_parse = _parse_operators(seq[index:], precedence + (0 if rassoc else 1))
        if rhs_parse is None:
            raise AssertionError()
        if isinstance(rhs_parse, ParseFailure):
            return rhs_parse
        rhs, num_tokens = rhs_parse

        index += num_tokens
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
    container -- the context in which seq appears ('root', 'parentheses', or 'brackets')
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
    # Statements look like
    #   variable eq expression
    #   assert expression
    #   die

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
            return token

    else:
        failure = token

    if note is None:
        i = lambda s: f'\x1B[3m{s}\x1B[23m'
        note = f'statements must be “{i("variable")} = {i("expression")}”,' \
                f' “assert {i("expression")}”, or “die”'
    return ParseFailure('invalid statement', failure, note)

#~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~

if __name__ == '__main__':

    def prompt():
        print("\x1B[2mparse:\x1B[22m", end=' ')
        line = input()
        if line in ['exit', 'quit']:
            exit()
        return line + "\n"

    stream = TokenStream("", prompt)

    while True:
        result = parse_statement(stream)
        if result is None:
            pass
        elif isinstance(result, ParseFailure):
            result.show(stream.log())
            stream.clear_line()
        else:
            result.show()
