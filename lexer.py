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

KEYWORDS = {
    'and':    'and',
    'or':     'or',
    'not':    'not',
    'len':    'len',
    'true':   None,
    'false':  None,
    'die':    None,
    'assert': None,
}

wsp = re.compile(r'\s+')
nmp = re.compile(r'\d+')
vxp = re.compile(r'([_a-zA-Z][_a-zA-Z0-9]*\??)(:(?:0+|[+-−]\d+))?')
# vxp = re.compile(r'([_a-zA-Z][_a-zA-Z0-9]*\??)(:(?:0+|[+-−]\d+)|@\d+)?')

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

    def extract(self):
        return [self]

    def show(self):
        print(self)

class ParseFailure:
    def __init__(self, msg, hi=None, note=None):
        """
        msg -- string describing the failure
        hi  -- token or parse tree to highlight
        """
        self.message = msg
        self.highlight = hi
        self.note = note

    def __str__(self):
        return f"\x1B[91merror\x1B[39m: {self.message}"

    def show(self, log):
        """
        log -- a copy of the text prior to tokenization (split into lines)
        """
        if self.highlight is None:
            print(f"\x1B[91merror\x1B[39m: {self.message}")
            return
        if isinstance(self.highlight, tuple):
            tokens = sum((x.extract() for x in self.highlight), [])
        else:
            tokens = self.highlight.extract()
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
        if self.note is not None:
            print(f"\x1B[94mnote\x1B[39m: {self.note}")

#~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~

class TokenStream:
    def __init__(self, text, more=None):
        """
        text -- text to be tokenized
        more -- nullary function that will be called to get more text
        """
        self.text     = text
        self.more     = more
        self.line     = 1
        self.column   = 1
        self.newline  = False
        self.buffer   = []
        self._log     = [text]
        self.complete = False

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
        if self.complete:
            return None
        while True:
            # Strip leading whitespace or emit a newline token
            match = wsp.match(self.text)
            if match is not None:
                ln, co = self.line, self.column
                newline = self._advance(match.group())
                self.text = self.text[match.end():]
                if newline and not self.newline:
                    self.newline = True
                    token = Token(None, 'newline', None, ln, co)
                    self.buffer.append(token)
                    return token

            if len(self.text) == 0:
                if self.more is None:
                    self.complete = True
                    return None
                addendum = self.more()
                if addendum is None:
                    self.complete = True
                    return None
                self.text = addendum
                self._log.append(addendum)
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
                            self.complete = True
                            return None
                        addendum = self.more()
                        if addendum is None:
                            self.complete = True
                            return None
                        self.text = addendum
                        self._log.append(addendum)
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
                    symbol = KEYWORDS[word.lower()]
                    if symbol is None:
                        token = Token(word.lower(), 'keyword', word, ln, co)
                    else:
                        token = Token(symbol, 'symbol', word, ln, co)
                    self.buffer.append(token)
                    return token

                index = match.group(2)
                if index is None:
                    value = (word, None)
                else:
                    offset = int(index[1:])
                    value = (word, offset)

                self._advance(match.group())
                self.text = self.text[match.end():]
                token = Token(value, 'variable', match.group(), ln, co)
                self.buffer.append(token)
                return token

            # Integers
            match = nmp.match(self.text)
            if match is not None:
                numr = match.group()
                self._advance(numr)
                self.text = self.text[match.end():]
                token = Token(int(numr), 'number', numr, ln, co)
                self.buffer.append(token)
                return token

            # Atoms
            if self.text.startswith(STRDELIM):
                point = Token(None, None, None, ln, co)
                offset = 1
                escape = False
                value = []
                while True:
                    if not offset < len(self.text):
                        if self.more is None:
                            self._advance(self.text)
                            self.text = ""
                            self.complete = True
                            return ParseFailure('unterminated string', point)
                        addendum = self.more()
                        if addendum is None:
                            self._advance(self.text)
                            self.text = ""
                            self.complete = True
                            return ParseFailure('unterminated string', point)
                        self.text += addendum
                        self._log.append(addendum)
                        continue
                    char = self.text[offset]
                    if escape:
                        replacement = ESCAPESEQ.get(char, None)
                        if replacement is None:
                            self._advance(self.text)
                            self.text = ""
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
                token = Token(value, 'atom', verbatim, ln, co)
                self.buffer.append(token)
                return token

            # Symbols
            for pair in SYMBOLPAIRS:
                if self.text.startswith(pair):
                    self._advance(pair)
                    self.text = self.text[2:]
                    token = Token(SYMBOLPAIRS[pair], 'symbol', pair, ln, co)
                    self.buffer.append(token)
                    return token

            for sym in SYMBOLS:
                if self.text.startswith(sym):
                    self._advance(sym)
                    self.text = self.text[1:]
                    token = Token(SYMBOLS[sym], 'symbol', sym, ln, co)
                    self.buffer.append(token)
                    return token

            if self.text[0] == ':':
                match = nmp.match(self.text[1:])
                if match is None:
                    note = 'a signed numeric literal is required after “:”'
                else:
                    numr = match.group()
                    note = f'a sign is required: “\x1B[94m+\x1B[39m{numr}”' \
                            f' or “\x1B[94m−\x1B[39m{numr}”'
            else:
                note = None

            self._advance(self.text)
            self.text = ""
            self.newline = True
            point = Token(None, None, None, ln, co)
            return ParseFailure('invalid token', point, note)

    def clear_line(self):
        while True:
            if self.newline:
                break
            token = next(self)
            if token is None:
                return
            if isinstance(token, ParseFailure):
                return

    def __len__(self):
        return len(self.buffer)

    def __getitem__(self, idx):
        if idx < 0:
            raise IndexError()
        if not idx < len(self.buffer):
            for _ in range(idx - len(self.buffer) + 1):
                token = next(self)
                if isinstance(token, ParseFailure):
                    return token
                if token is None:
                    break
        return self.buffer[idx]

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
        token = next(stream)
        if token is None:
            break
        if isinstance(token, ParseFailure):
            token.show(stream.log())
        else:
            print(token)
