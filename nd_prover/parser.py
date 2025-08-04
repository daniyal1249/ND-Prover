import re

from .logic import *


class ParsingError(Exception):
    pass


class Symbols:
    symbols = {
        'not': '¬',
        '~': '¬',
        '∼': '¬',
        '-': '¬',
        '−': '¬',
        'and': '∧',
        '^': '∧',
        '&': '∧',
        '.': '∧',
        '·': '∧',
        '*': '∧',
        'or': '∨',
        'iff': '↔',
        '≡': '↔',
        '<->': '↔',
        'implies': '→',
        '⇒': '→',
        '⊃': '→',
        '->': '→',
        '>': '→',
        'forall': '∀',
        '⋀': '∀',
        'exists': '∃',
        '⋁': '∃',
        'falsum': '⊥',
        'XX': '⊥',
        '#': '⊥',
        'box': '□',
        '[]': '□',
        'dia': '♢',
        '<>': '♢',
    }

    keys = sorted(symbols, key=len, reverse=True)
    patterns = [re.escape(k) for k in keys]
    patterns.append(r'A(?=[a-z])')  # Forall
    patterns.append(r'E(?=[a-z])')  # Exists
    pattern = '|'.join(patterns)
    regex = re.compile(pattern)

    @classmethod
    def sub(cls, s):
        def repl(m):
            match = m.group(0)
            if match == 'A':
                return '∀'
            if match == 'E':
                return '∃'
            return cls.symbols[match]
        return cls.regex.sub(repl, s)
    

def split_line(line):
    parts = [s.strip() for s in re.split(r'[;|]', line)]
    if len(parts) != 2:
        raise ParsingError('Must provide justification separated by ";" or "|".')
    return parts


def strip_parens(s):
    while s and s[0] == '(' and s[-1] == ')':
        depth = 0
        for i, c in enumerate(s):
            if c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0 and i != len(s) - 1:
                    return s
        s = s[1:-1]
    return s


def find_main_connective(s, symbol):
    depth = 0
    for i in range(len(s) - 1, -1, -1):
        if s[i] == ')':
            depth += 1
        elif s[i] == '(':
            depth -= 1
        elif depth == 0 and s[i] == symbol:
            return i
    return -1


def parse_term(t):
    return Const(t) if t in Const.names else Var(t)


def _parse_formula(f):
    f = strip_parens(f)
    
    # Falsum
    if f == '⊥':
        return Falsum()
    
    # Prop vars
    m = re.fullmatch(r'[A-Z]', f)
    if m:
        return PropVar(f)
    
    # Predicates
    m = re.fullmatch(r'([A-Z])([a-z]+)', f)
    if m:
        args = [parse_term(t) for t in m.group(2)]
        return Pred(m.group(1), args)

    # Equality
    m = re.fullmatch(r'([a-z])=([a-z])', f)
    if m:
        left = parse_term(m.group(1))
        right = parse_term(m.group(2))
        return Eq(left, right)

    # Binary connectives
    connectives = [('↔', Iff), ('→', Imp), ('∨', Or), ('∧', And)]

    for sym, cls in connectives:
        idx = find_main_connective(f, sym)
        if idx == -1:
            continue
        left = _parse_formula(f[:idx])
        right = _parse_formula(f[idx + 1:])
        return cls(left, right)
    
    # Negation
    if f.startswith('¬'):
        return Not(_parse_formula(f[1:]))
    
    # Quantifiers
    v1, v2 = Var.names[0], Var.names[-1]
    m = re.match(f'(∀|∃)([{v1}-{v2}])', f)
    if m:
        var = Var(m.group(2))
        inner = _parse_formula(f[2:])
        if m.group(1) == '∀':
            return Forall(var, inner)
        return Exists(var, inner)

    # Modal operators
    if f.startswith('□'):
        return Box(_parse_formula(f[1:]))
    if f.startswith('♢'):
        return Dia(_parse_formula(f[1:]))

    raise ParsingError(f'Could not parse formula: "{f}".')


def parse_formula(f):
    f = ''.join(Symbols.sub(f).split())
    return _parse_formula(f)


def parse_assumption(a):
    a = ''.join(Symbols.sub(a).split())
    if a == '□':
        return BoxMarker()
    return _parse_formula(a)


def parse_rule(rule):
    rule = ''.join(Symbols.sub(rule).split())
    for r in Rules.rules:
        if r.name == rule:
            return r
    raise ParsingError(f'Could not parse rule of inference: "{rule}".')


def parse_citations(citations):
    citations = ''.join(citations.split())

    c_list = []
    for c in citations.split(','):
        m = re.fullmatch(r'(\d+)-(\d+)', c)
        if m:
            pair = (int(m.group(1)), int(m.group(2)))
            c_list.append(pair)
            continue
        try:
            c_list.append(int(c))
        except ValueError:
            raise ParsingError(f'Could not parse citations: "{citations}".')
    return c_list


def parse_justification(j):
    parts = j.split(',', maxsplit=1)
    r = parse_rule(parts[0])
    if len(parts) == 1:
        return Justification(r, [])
    c = parse_citations(parts[1])
    return Justification(r, c)


def parse_line(line):
    f, j = split_line(line)
    return parse_formula(f), parse_justification(j)
