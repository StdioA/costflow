from datetime import date, datetime, timedelta
from dateutil import parser as dateparse
from decimal import Decimal, InvalidOperation
from .definitions import (
    Balance, KVEntry, Option, Pad, Transaction,
    Payee, Narration, Posting, Comment, UnaryEntry,
)
from ply import lex, yacc


# TODO: Implement other commands (price & formula)
# TODO: Fallback rules for formula & comments
reserved = {
    'open': 'OPEN',
    'close': 'CLOSE',
    'commodity': 'COMMODITY',
    'balance': 'BALANCE',
    'pad': 'PAD',
    # 'price': 'PRICE',
}

kv_directives = {
    'option': 'OPTION',
    'note': 'NOTE',
    'event': 'EVENT',
}

# States
states = [
    ('transaction', 'exclusive'),
    ('comment', 'exclusive'),
    ('const', 'inclusive'),
    ('kvkey', 'inclusive'),
    ('anyvalue', 'exclusive'),
]

# Tokens
tokens = [
    "NAME", "AMOUNT", "DATE", "COMMENT",
    "NUMBER", "STRING",
] + list(reserved.values()) + list(kv_directives.values())

literals = "@!*|+>"


@lex.Token(f"({'|'.join(reserved.keys())})")
def t_RESERVED(t):
    type_ = reserved.get(t.value, None)
    if type_:
        t.type = reserved.get(t.value, None)
        t.lexer.push_state("const")
        return t
    # Fallback (may be useless)
    t.type = "STRING"
    return t_STRING(t)


@lex.Token(f"({'|'.join(kv_directives.keys())})")
def t_KV(t):
    type_ = kv_directives.get(t.value, None)
    if type_:
        t.type = type_
        t.lexer.push_state("kvkey")
        return t
    # Fallback (may be useless)
    t.type = "STRING"
    return t_STRING(t)


def t_DATE(t):
    r"[0-9]{4,}[\-/][0-9]+[\-/][0-9]+"
    t.value = dateparse.parse(t.value).date()
    return t


def t_DATE_ABBR(t):
    r"^(yesterday|ytd|dby|tomorrow|tmr|dat)"
    date_abbr = {
        "dby": -2,
        "yesterday": -1,
        "ytd": -1,
        "tomorrow": 1,
        "tmr": 1,
        "dat": 2,
    }
    today = datetime.today().date()
    t.type = "DATE"
    t.value = today + timedelta(date_abbr.get(t.value, 0))
    return t


_month_abbrs = "|".join(m[0] for m in dateparse.parserinfo.MONTHS)


# Parse date like "%b %d" (e.g. "Jan 01")
@lex.TOKEN(rf"^({_month_abbrs})\s?([12][0-9]|3[0-1]|0?[1-9])")
def t_DATE_MD(t):
    t.type = "DATE"
    t.value = dateparse.parse(t.value).date()
    return t


def t_PIPE(t):
    r'\|'
    t.type = '|'
    t.lexer.begin("transaction")
    return t


def t_STRING(t):
    r'[\w,:\.]+'
    value = t.value

    # Check if any value is needed
    # e.g. OPTION -> (kvkey) some_key -> (anyvalue) one two three
    if t.lexer.current_state() == 'kvkey':
        t.lexer.push_state("anyvalue")
        return t

    try:
        v = Decimal(value)
        t.type = "NUMBER"
        t.value = v
        return t_NUMBER(t)
    except InvalidOperation:
        pass
    return t


def t_STRING_LETERAL(t):
    r'\"([^\\\"]|\\.)*\"'
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

    if t.lexer.current_state() == "INITIAL":
        t.lexer.push_state("transaction")
    if t.lexer.current_state() == "transaction":
        t.type = "AMOUNT"
    return t


def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")


t_ignore = " \t"


def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)


def t_COMMENT(t):
    r'(;|//)\s+'
    t.lexer.begin("comment")
    return t


# Exclusive tokens for transaction state
t_transaction_NAME = t_STRING
t_transaction_AMOUNT = t_NUMBER

t_ANY_newline = t_newline
t_ANY_ignore = t_ignore
t_ANY_error = t_error


# Exclusive tokens for comment state
t_comment_STRING = r".+"
t_comment_ignore = ""
t_comment_error = t_error


# Exclusive tokens for anyvalue state
t_anyvalue_STRING = r".+"
t_anyvalue_LETERAL = t_STRING_LETERAL

# Statements
precedence = (
    ('right', '@'),
)


def p_entry_transaction(t):
    "entry : transaction"
    t[1].build()
    t[0] = t[1]


def p_entry_open_close(t):
    """entry : comment
             | open
             | close
             | note
             | balance
             | pad"""
    t[1].build()
    t[0] = t[1]


def p_normal_entry(t):
    """entry : option
             | event
             | commodity"""
    t[0] = t[1]


# Expressions
# --- Transaction ---
def p_payee(t):
    "payee : '@' STRING"
    t[0] = Payee(t[2])


def p_narration(t):
    """narration : payee
                 | STRING STRING
                 | payee STRING
                 | STRING
                 | '*' narration
                 | '!' narration
                 | DATE narration"""

    if isinstance(t[1], date):
        t[2].date_ = t[1]
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
                    | rev_postings '+' rev_posting
    """
    if len(t) == 2:
        t[0] = [t[1]]
    else:
        t[1].append(t[3])
        t[0] = t[1]


def p_transaction(t):
    """transaction : narration rev_postings
                   | transaction '>' rev_postings
                   | narration '|' posting
                   | transaction '|' posting
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
    t[0] = trx


# --- Comment ---
def p_comment(t):
    """comment : COMMENT STRING"""
    t[0] = Comment(t[2])


# --- Open & Close ---
def p_open_close(t):
    """open : OPEN STRING
            | DATE open
       close : CLOSE STRING
             | DATE close
       commodity : COMMODITY STRING
                 | DATE commodity"""
    if isinstance(t[1], date):
        t[2].date_ = t[1]
        t[0] = t[2]
    else:
        t[0] = UnaryEntry(t[1], t[2])


# --- Option ---
def p_option(t):
    """option : OPTION STRING STRING
    """
    if len(t) == 4:
        # Init option
        t[0] = Option(t[2], t[3])
    else:
        t[1].value += f" {t[2]}"
        t[0] = t[1]


def p_event_note(t):
    """event : EVENT STRING STRING
             | DATE event
       note  : NOTE STRING STRING
             | DATE note"""
    if isinstance(t[1], date):
        t[2].date_ = t[1]
        t[0] = t[2]
    elif len(t) == 4:
        t[0] = KVEntry(t[1], t[2], t[3])
    else:
        t[1].value += f" {t[2]}"
        t[0] = t[1]


def p_balance(t):
    """balance : BALANCE STRING NUMBER
               | DATE balance
               | balance STRING"""
    if len(t) == 4:
        t[0] = Balance(t[2], t[3])
    elif isinstance(t[1], date):
        t[2].date_ = t[1]
        t[0] = t[2]
    else:
        t[1].currency = t[2]
        t[0] = t[1]


def p_pad(t):
    """pad : PAD STRING STRING
           | DATE pad"""
    if len(t) == 4:
        t[0] = Pad(t[2], t[3])
    else:
        t[2].date_ = t[1]
        t[0] = t[2]


def p_error(t):
    print("Syntax error at '%s'" % t)


parser = yacc.yacc()

# ----- main -----
if __name__ == '__main__':
    inputs = [
        "tomorrow Jan 01 dby",
        "Dec 9 desc 100 from > to",
    ]
    for s in inputs:
        parser = yacc.yacc()
        print("input:", s)
        t = parser.parse(s, lexer=lex.lex(), debug=False)
        print("RESULT", t)
        print()

        # lexer = lex.lex()
        # lexer.input(s)
        # for tok in lexer:
        #     print(tok)
        # print()
