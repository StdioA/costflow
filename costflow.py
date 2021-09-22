from datetime import date
from dateutil import parser as dateparse
from decimal import Decimal, InvalidOperation
from definitions import Transaction, Payee, Narration, Posting


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
    ('transaction','exclusive'),
)

# Tokens
tokens = [
    "NUMBER", "STRING", "LT", "PIPE", "ADD",
    "NAME", "AMOUNT", "DATE",
    "AT", "EXCLAMATION", "ASTERISK"
] + list(reserved.values())


t_AT = "@"
t_EXCLAMATION = r"\!"
t_ASTERISK = r"\*"


def t_DATE(t):
    r"[0-9]{4,}[\-/][0-9]+[\-/][0-9]+"
    t.value = dateparse.parse(t.value).date()
    return t


def t_PIPE(t):
    r'\|'
    t.lexer.begin("transaction")
    return t


def t_STRING(t):
    r'[\w:]+'
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
    t.lexer.begin("transaction")
    t.type = "AMOUNT"
    return t


def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")


t_ignore = " \t"


def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)


# Exclusive tokens for transaction state
t_transaction_LT    = r'>'
t_transaction_ADD = r"\+"
t_transaction_NAME = t_STRING            # TODO: 按照 beancount 的 lexer 处理
t_transaction_AMOUNT = t_NUMBER
t_transaction_PIPE = t_PIPE

t_transaction_newline = t_newline
t_transaction_ignore = t_ignore
t_transaction_error = t_error


# Statements
precedence = (
    ('right', 'AT'),
)


def p_statement_narration(t):
    "statement : transaction"
    t[1].build()
    t[0] = t[1]

# Expressions
def p_expression_payee(t):
    "payee : AT STRING"
    t[0] = Payee(t[2])


def p_expression_narration(t):
    """narration : payee
                 | STRING STRING
                 | payee STRING
                 | STRING
                 | ASTERISK narration
                 | EXCLAMATION narration
                 | DATE narration"""

    if isinstance(t[1], date):
        t[2].date = t[1]
        t[0] = t[2]
        return
    
    if t[1] in ("*", "!"):
        t[2].type_ = t[1]
        t[0] = t[2]
        return

    if len(t) == 3:
        payee = t[1]
        if not isinstance(payee, Payee):
            payee = Payee(payee)
        t[0] = Narration(payee=payee, desc=t[2])
    elif isinstance(t[1], Payee):
        t[0] = Narration(payee=t[1], desc="")
    else:
        t[0] = Narration(payee=Payee(""), desc=t[1])


def p_posting(t):
    """posting : NAME NAME AMOUNT
               | NAME AMOUNT
    """
    if len(t) == 3:
        t[0] = Posting(t[1], t[2])
    else:
        t[0] = Posting(t[1], t[3], t[2])


def p_rev_posting(t):
    """rev_posting : AMOUNT NAME NAME
                   | NAME NAME
                   | AMOUNT NAME
                   | NAME
    """
    if len(t) == 2:
        t[0] = Posting(account=t[1], amount=None)
    elif len(t) == 3:
        if isinstance(t[1], Decimal):
            t[0] = Posting(account=t[2], amount=t[1])
        else:
            t[0] = Posting(account=t[2], currency=t[1])
    else:
        t[0] = Posting(t[3], t[1], t[2])    # amount currency account

def p_rev_postings(t):
    """rev_postings : rev_posting
                    | rev_postings ADD rev_posting
    """
    if len(t) == 2:
        t[0] = [t[1]]
    else:
        t[1].append(t[3])
        t[0] = t[1]

def p_transaction(t):
    """transaction : narration rev_postings
                   | transaction LT rev_postings
                   | narration PIPE posting
                   | transaction PIPE posting
    """
    trx = t[1]
    if not isinstance(trx, Transaction):
        trx = Transaction(t[1])

    if t[2] == '|':
        # deal with posting pipe
        trx.push(t[3])
    else:
        # deal with rev_posting group
        if t[2] == '>':
            postings = t[3]
        else:
            postings = t[2]
        for posting in postings:
            trx.push(posting)
        trx.rebalance()
    t[0] = trx


def p_error(t):
    print("Syntax error at '%s'" % t.value)


# ----- main -----
import ply.lex as lex
import ply.yacc as yacc

s = '! @abc def -100 from + 300 CNY from2 > USD to1 + to2'
parser = yacc.yacc()
print("input:", s)
t = parser.parse(s, lexer=lex.lex())
print(t.render())

print()
s = '''2021-09-24 麦当劳 汉堡
    | from 24 | to -18 
    | to2 -6'''
parser = yacc.yacc()
print("input:", s)
t = parser.parse(s, lexer=lex.lex())
print(t.render())

# lexer = lex.lex()
# lexer.input(s)
# while True:
#     tok = lexer.token()
#     if tok is None:
#         break
#     print(tok)
