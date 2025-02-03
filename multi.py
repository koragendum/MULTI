from lexer  import *
from parser import *
from engine import *

statements = []

def prompt():
    while True:
        print("\x1B[2m>\x1B[22m", end=' ')
        line = input()
        stripped = line.strip()
        if stripped in ('exit', 'quit'):
            exit()
        if stripped == 'show':
            count = reindex(statements)
            for s in statements:
                print(s)
            continue
        if stripped == 'run':
            count = reindex(statements)
            out = {}
            run_code_to_completion(statements, Environment(count), out)
            for _, msgs in out.items():
                for msg in msgs:
                    print(msg)
            continue
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
        reified = reify(result)
        if isinstance(reified, ParseFailure):
            reified.show(stream.log())
        else:
            statements.append(reified)
