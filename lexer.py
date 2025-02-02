import re

COMMENT = ['//', '--', '\u203B']

STRDELIM  = '"'

STRESCAPE = '\\'

ESCAPESEQ = {
    STRESCAPE:  STRESCAPE,
    STRDELIM:   STRDELIM,
    'n':        '\n',
    't':        '\t',
    'r':        '\r',
    'e':        '\x1B',
}

SYMBOLS = {
    '(': 'pL',
    ')': 'pR',
    '[': 'bL',
    ']': 'bR',
    '+': 'add',         # addition, concatenation, and position
    '−': 'sub',         # subtraction and negation
    '-': 'sub',         # subtraction and negation
    '×': 'mul',         # multiplication
    '*': 'mul',         # multiplication
    '/': 'div',         # division
    '÷': 'div',         # division
    '%': 'mod',         # modulo or remainder
    '=': 'eq',          # assignment and equal
    '≠': 'neq',         # not equal
    '≥': 'geq',         # greater or equal
    '≤': 'leq',         # less or equal
    '>': 'gt',          # greater
    '<': 'lt',          # less
    '∧': 'and',         # conjunction (logical-and and minimum)
    '∨': 'or',          # disjunction (logical-or and maximum)
    '!': 'not',         # negation
    '.': 'idx',         # index
    '#': 'len',         # length
    '?': 'def',         # defined
    '~': 'def',         # defined
    ',': 'sepr',        # separator
}

SYMBOLPAIRS = {
    '==': 'eq',         # equal
    '!=': 'neq',        # not equal
    '>=': 'geq',        # greater or equal
    '<=': 'leq',        # less or equal
    '=<': 'leq',        # less or equal
}

KEYWORDS = ['and', 'or', 'not', 'len', 'die', 'if']

wsp = re.compile(r'\s+')
nmp = re.compile(r'\d+')
vxp = re.compile(r'([_a-zA-Z][_a-zA-Z0-9]*\??)(:(?:0|[+-−]\d+)|@\d+)?')

# We support x@0 notation for debugging.

#~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~

class Token:
    def __init__(self, value, kind, text, line, column):
        self.value  = value
        self.kind   = kind
        self.text   = text
        self.line   = line
        self.column = column

    def __str__(self):
        tk = '\x1B[38;5;42mToken\x1B[39m'
        if self.value is None:
            return f'{tk} : {self.kind} @ {self.line},{self.column}'
        value = repr(self.value) if self.kind == 'atom' else self.value
        return f'{tk} {value} : {self.kind} @ {self.line},{self.column}'

    def show(self):
        print(self)

class ParseTree:
    def __init__(self, label, children):
        self.label = label
        self.children = children

    def __str__(self):
        tr = "\x1B[38;5;129mTree\x1B[39m"
        return f"{tr} {self.label}"

    def __len__(self):
        return len(self.children)

    def __iter__(self):
        return iter(self.children)

    def __getitem__(self, x):
        return self.children[x]

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

def extract_tokens(obj):
    if isinstance(obj, Token):
        return [obj]
    if isinstance(obj, ParseTree):
        return sum((extract_tokens(x) for x in obj.children), [])
    if isinstance(obj, (list, tuple)):
        return sum((extract_tokens(x) for x in obj), [])
    raise RuntimeError(f"unable to extract tokens from {type(obj)}")

class ParseFailure:
    def __init__(self, msg, hi=None):
        """
        msg -- string describing the failure
        hi  -- token or parse tree to highlight
        """
        self.message = msg
        self.highlight = hi

    def __str__(self):
        return f"\x1B[91merror\x1B[39m: {self.message}"

    def show(self, log):
        """
        log -- a copy of the text prior to tokenization (split into lines)
        """
        if self.highlight is None:
            print(f"\x1B[91merror\x1B[39m: {self.message}")
            return
        tokens = extract_tokens(self.highlight)
        lnum = tokens[0].line
        print(f"\x1B[91merror\x1B[39m: line {lnum}: " + self.message)
        for idx, tok in enumerate(tokens):
            if tok.line != lnum: break
            last = idx
        line = log[lnum - 1]
        margin = "\x1B[2m\u2502\x1B[22m "
        print(margin)
        text = tokens[last].text
        span  = 1 if text is None else len(text)
        left  = tokens[0].column - 1
        right = tokens[last].column - 1 + span
        l, m, r = line[:left], line[left:right], line[right:]
        print(f'{margin}{l}\x1B[91m{m}\x1B[39m{r}')
        print(margin, end='')
        print(" "*left, end='')
        print("\x1B[91m^", end='')
        print("~"*(right-left-1), end='')
        print("\x1B[39m", end='')
        print()

#~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~

class TokenStream:
    def __init__(self, text, more=None):
        """
        text -- text to be tokenized
        more -- nullary function that will be called to get more text
        """
        self.text    = text
        self.more    = more
        self.line    = 1
        self.column  = 1
        self.newline = False
        self._log    = [text]

    def log(self):
        return ''.join(self._log).split('\n')

    def _advance(self, string):
        newlines = string.count('\n')
        if newlines == 0:
            self.column = self.column + len(string)
            return False
        else:
            self.line = self.line + newlines
            self.column = len(string) - string.rindex('\n')
            return True

    def __next__(self):
        while True:
            # Strip leading whitespace or emit a newline token
            match = wsp.match(self.text)
            if match is not None:
                ln, co = self.line, self.column
                newline = self._advance(match.group())
                self.text = self.text[match.end():]
                if newline and not self.newline:
                    self.newline = True
                    return Token(None, 'newline', None, ln, co)

            if len(self.text) == 0:
                if self.more is None:
                    return None
                self.text = self.more()
                if self.text is None:
                    return None
                self._log.append(self.text)
                continue

            if any(self.text.startswith(cs) for cs in COMMENT):
                while True:
                    if '\n' in self.text:
                        end = self.text.index('\n')
                        self._advance(self.text[:end])
                        self.text = self.text[end:]
                        break
                    else:
                        self._advance(self.text)
                        if self.more is None:
                            self.text = None
                            return None
                        self.text = self.more()
                        if self.text is None:
                            return None
                        self._log.append(self.text)
                continue

            # We’re guaranteed not to return a newline
            self.newline = False
            ln, co = self.line, self.column

            # Variables
            match = vxp.match(self.text)
            if match is not None:
                word = match.group(1)
                if word in KEYWORDS:
                    self._advance(word)
                    self.text = self.text[match.end(1):]
                    return Token(word, 'keyword', word, ln, co)

                index = match.group(2)
                if index is None:
                    value = (word, None, None)
                else:
                    mode = 'abs' if index[0] == '@' else 'rel'
                    offset = int(index[1:])
                    value = (word, mode, offset)

                self._advance(match.group())
                self.text = self.text[match.end():]
                return Token(value, 'variable', match.group(), ln, co)

            # Integers
            match = nmp.match(self.text)
            if match is not None:
                numr = match.group()
                self._advance(numr)
                self.text = self.text[match.end():]
                return Token(int(numr), 'number', numr, ln, co)

            # Atoms
            if self.text.startswith(STRDELIM):
                point = Token(None, None, None, ln, co)
                offset = 1
                escape = False
                value = []
                while True:
                    if not offset < len(self.text):
                        if self.more is None:
                            return ParseFailure('unterminated string', point)
                        addendum = self.more()
                        if addendum is None:
                            point = Token(None, None, None, ln, co)
                            return ParseFailure('unterminated string', point)
                        self.text += addendum
                        self._log.append(addendum)
                        continue
                    char = self.text[offset]
                    if escape:
                        replacement = ESCAPESEQ.get(char, None)
                        if replacement is None:
                            msg = 'string contains invalid escape sequence' \
                                    f' “{STRESCAPE}{char}”'
                            return ParseFailure(msg, point)
                        else:
                            value.append(replacement)
                        escape = False
                    elif char == STRESCAPE:
                        escape = True
                    elif char == STRDELIM:
                        offset += 1
                        break
                    else:
                        value.append(char)
                    offset += 1
                verbatim = self.text[:offset]
                self._advance(verbatim)
                self.text = self.text[offset:]
                value = ''.join(value)
                return Token(value, 'atom', verbatim, ln, co)

            # Symbols
            for pair in SYMBOLPAIRS:
                if self.text.startswith(pair):
                    self._advance(pair)
                    self.text = self.text[2:]
                    return Token(SYMBOLPAIRS[pair], 'symbol', pair, ln, co)

            for sym in SYMBOLS:
                if self.text.startswith(sym):
                    self._advance(sym)
                    self.text = self.text[1:]
                    return Token(SYMBOLS[sym], 'symbol', sym, ln, co)

            point = Token(None, None, None, ln, co)
            return ParseFailure('invalid token', point)

class TokenBuffer:
    def __init__(self, stream, more=None):
        """
        stream -- text or instance of TokenStream
        more   -- nullary function that will be called to get more text
        """
        if isinstance(stream, str):
            self.stream = TokenStream(stream, more)
        else:
            self.stream = stream
        self.buffer = []
        self.is_complete = False

    def __len__(self):
        if self.is_complete:
            return len(self.buffer)
        raise AssertionError("length unknown because buffer has not been completed")

    def __getitem__(self, idx):
        if self.is_complete:
            return self.buffer[idx]
        if idx < 0:
            raise IndexError("length unknown because buffer has not been completed")
        if idx >= len(self.buffer):
            for _ in range(idx - len(self.buffer) + 1):
                tok = next(self.stream)
                if tok is None:
                    self.is_complete = True
                    break
                self.buffer.append(tok)
        return self.buffer[idx]

    def complete(self):
        while (tok := next(self.stream)) is not None:
            self.buffer.append(tok)
        self.is_complete = True

#~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~

if __name__ == '__main__':

    def prompt():
        print("\x1B[2mlex:\x1B[22m", end=' ')
        line = input()
        if line in ['exit', 'quit']:
            exit()
        return line + "\n"

    stream = TokenStream("", prompt)

    while True:
        tok = next(stream)
        if isinstance(tok, ParseFailure):
            tok.show(stream.log())
            break
        print(tok)
