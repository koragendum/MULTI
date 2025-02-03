from lexer  import *
from parser import *
from engine import *

def prompt():
    print("\x1B[2m>\x1B[22m", end=' ')
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
        reified = reify(result)
        if isinstance(reified, ParseFailure):
            reified.show(stream.log())
        else:
            statements.append(reified)
            count = reindex(statements)
            out = {}
            run_code_to_completion(statements, Environment(count), out)
            for _, msgs in out.items():
                for msg in msgs:
                    print(msg)
