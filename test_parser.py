import pytest
from datetime import datetime
import costflow
from ply import lex, yacc
from definitions import Balance, KVEntry, Option, Pad, Transaction, Comment, UnaryEntry


@pytest.fixture
def parser():
    return yacc.yacc(module=costflow)


@pytest.fixture
def lexer():
    return lex.lex(module=costflow)


def test_transaction(parser, lexer):
    today = datetime.today().date()
    s = '! @abc "def ghi" -100 USD from + 300 CNY from2 > USD to1 + CNY to2'
    exp = f'''\
{today} ! "abc" "def ghi"
\tfrom\t-100.00 USD
\tfrom2\t300.00 CNY
\tto1\t100.00 USD
\tto2\t-300.00 CNY'''
    trx = parser.parse(s, lexer=lexer)
    assert trx.render() == exp


def test_pipe_transaction(parser, lexer):
    pipe_s = '2021-09-24 麦当劳 汉堡\n| from 24 | to -18\n| to2 -6'
    pipe_exp = '''\
2021-09-24 * "麦当劳" "汉堡"
\tfrom\t24.00 CNY
\tto\t-18.00 CNY
\tto2\t-6.00 CNY'''
    trx = parser.parse(pipe_s, lexer=lexer)
    assert isinstance(trx, Transaction)
    assert trx.render() == pipe_exp


def test_comments(parser, lexer):
    inputs = (
        "; hi hi hi hello",
        "// hi hi hi hello",
    )
    exp = "; hi hi hi hello"
    for i in inputs:
        cmt = parser.parse(i, lexer=lexer.clone())
        assert isinstance(cmt, Comment)
        assert cmt.render() == exp
        parser.restart()


def test_open_and_close(parser, lexer):
    today = datetime.today().date()
    testcases = (
        ("open Assets:Bank", f"{today} open Assets:Bank"),
        ("2021-01-01 close Assets:Bank", "2021-01-01 close Assets:Bank"),
    )
    for tc in testcases:
        cmt = parser.parse(tc[0], lexer=lexer.clone())
        assert isinstance(cmt, UnaryEntry)
        assert cmt.render() == tc[1]
        parser.restart()


def test_commodity(parser, lexer):
    today = datetime.today().date()
    testcases = (
        ("commodity CAD", f"{today} commodity CAD"),
        ("1867-01-01 commodity CAD", "1867-01-01 commodity CAD"),
    )
    for tc in testcases:
        cmt = parser.parse(tc[0], lexer=lexer.clone())
        assert isinstance(cmt, UnaryEntry)
        assert cmt.render() == tc[1]
        parser.restart()


def test_option(parser, lexer):
    testcases = (
        ("option title Example Costflow file", 'option "title" "Example Costflow file"'),
        ("option operating_currency CNY", 'option "operating_currency" "CNY"'),
        ('option "conversion_currency" "NOTHING"', 'option "conversion_currency" "NOTHING"'),
    )
    for tc in testcases:
        cmt = parser.parse(tc[0], lexer=lexer.clone())
        assert isinstance(cmt, Option)
        assert cmt.render() == tc[1]
        parser.restart()


def test_event_and_note(parser, lexer):
    today = datetime.today().date()
    testcases = (
        ('2017-01-02 event "location" "Paris, France"', '2017-01-02 event "location" "Paris, France"'),
        ("event location Paris, France", f'{today} event "location" "Paris, France"'),
        ("2019-07-01 note bofa Called about fraudulent card.", '2019-07-01 note bofa "Called about fraudulent card."'),
        ("note bofa Called about fraudulent card.", f'{today} note bofa "Called about fraudulent card."'),
    )
    for tc in testcases:
        cmt = parser.parse(tc[0], lexer=lexer.clone())
        assert isinstance(cmt, KVEntry)
        assert cmt.render() == tc[1]
        parser.restart()


def test_balance(parser, lexer):
    today = datetime.today().date()
    testcases = (
        ('2017-01-01 balance Assets:BofA 360 USD', '2017-01-01 balance Assets:BofA 360 USD'),
        ("balance BofA 1024", f'{today} balance BofA 1024 CNY'),
    )
    for tc in testcases:
        cmt = parser.parse(tc[0], lexer=lexer.clone())
        assert isinstance(cmt, Balance)
        assert cmt.render() == tc[1]
        parser.restart()


def test_pad(parser, lexer):
    today = datetime.today().date()
    testcases = (
        ('2017-01-01 pad bofa eob', '2017-01-01 pad bofa eob'),
        ('pad bofa eob', f'{today} pad bofa eob'),
    )
    for tc in testcases:
        cmt = parser.parse(tc[0], lexer=lexer.clone())
        assert isinstance(cmt, Pad)
        assert cmt.render() == tc[1]
        parser.restart()
