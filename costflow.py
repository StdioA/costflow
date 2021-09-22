from decimal import Decimal, InvalidOperation
from dataclasses import dataclass

reserved = {
    'open' : 'OPEN',
    'close' : 'CLOSE',
    'commodity' : 'COMMODITY',
    'option' : 'OPTION',
    'note' : 'NOTE',
    'balance' : 'BALANCE',
    'pad' : 'PAD',
    'price' : 'PRICE',
    'event' : 'EVENT',
 }

# States
states = (
    ('transaction','inclusive'),
)

# Tokens
tokens = [
    "NUMBER", "AT", "STRING", "ASTERISK", "LT", "PIPE",
    "ACCOUNT"
] + list(reserved.values())

t_AT    = r'@'
t_ASTERISK    = r'\*'
t_LT    = r'>'
t_PIPE    = r'\|'

def t_STRING(t):
    r'\w+'
    value = t.value
    try:
        v = Decimal(value)
        t.type = "NUMBER"
        t.value = v
        return t_NUMBER(t)
    except InvalidOperation:
        pass
    return t

def t_STRING_LETERAL(t):
    r'\"([^\\\"]|\\.)*\" '
    t.type = "STRING"
    t.value = t.value[1:-1]
    t.lexpos += 1
    return t

def t_NUMBER(t):
    r'-?([0-9]+|[0-9][0-9,]+[0-9])(\.[0-9]*)?'
    try:
        t.value = Decimal(t.value)
    except ValueError:
        print("Integer value too large %d", t.value)
        t.value = 0
    t.lexer.push_state("transaction")
    return t

t_transaction_ACCOUNT = t_STRING

def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")
    
def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

t_ignore = " \t"

import ply.lex as lex
lexer = lex.lex()

precedence = (
    ('right', 'AT'),
    ('left', 'STRING', "NUMBER"),
)

class Payee:
    def __init__(self, s):
        self.payee = s
    
    def __repr__(self):
        return f"@{self.payee}"

def p_statemnet_account(t):
    'statement : ACCOUNT'
    print("account", t[1])

def p_statement_narration(t):
    'statement : transaction'
    print(t[1].render())


def p_expression_payee(t):
    "payee : AT STRING"
    t[0] = Payee(t[2])

def p_expression_narration(t):
    """narration : payee
                 | STRING STRING
                 | payee STRING
                 | STRING"""
    if len(t) == 3:
        payee = t[1]
        if not isinstance(payee, Payee):
            payee = Payee(payee)
        t[0] = (payee, t[2])
    elif isinstance(t[1], Payee):
        t[0] = (t[1], "")
    else:
        t[0] = (Payee(""), t[1])

@dataclass
class Posting:
    account: str
    amount: Decimal


class Transaction:
    def __init__(self, narration, account, amount):
        self.narration = narration
        self.postings = [Posting(account, amount)]

    def push(self, account, amount):
        self.postings.append(Posting(account, amount))

    def amount_left(self):
        amount = Decimal(0)
        for posting in self.postings:
            amount -= posting.amount
        return amount
    
    def render(self):
        lines = [f'2021-09-22 * "{self.narration[0].payee}" "{self.narration[1]}"']
        for posting in self.postings:
            # TODO: account finding
            # TODO: commodity
            lines.append("\t{}\t{:.2f} CNY".format(posting.account, posting.amount))
        return "\n".join(lines)


def p_transaction(t):
    """transaction : narration NUMBER ACCOUNT
                   | transaction LT ACCOUNT
    """
    if isinstance(t[2], Decimal):
        t[0] = Transaction(t[1], t[3], t[2])
    else:
        trans = t[1]
        trans.push(t[3], trans.amount_left())
        t[0] = trans

def p_error(t):
    print("Syntax error at '%s'" % t.value)

import ply.yacc as yacc
parser = yacc.yacc()

s = '@abc def -24.233 from > to'
# lexer.input(s)
# while True:
#     tok = lexer.token()
#     if tok is None:
#         break
#     print(tok)
parser.parse(s)
