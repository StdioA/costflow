from decimal import Decimal
import pytest
from datetime import date, datetime
import costflow
from ply import lex, yacc
from definitions import Balance, KVEntry, Option, Pad, Transaction, \
                        Payee, Narration, Posting, Comment, UnaryEntry


@pytest.fixture
def today():
    return datetime.today().date()


@pytest.fixture
def parser():
    return yacc.yacc(module=costflow)


@pytest.fixture
def lexer():
    return lex.lex(module=costflow)


def test_narration(parser, lexer):
    testcases = (
        ('desc', Narration(Payee(""), "desc")),
        ('@payee', Narration(Payee("payee"), "")),
        ('@payee desc', Narration(Payee("payee"), "desc")),
        ('payee desc', Narration(Payee("payee"), desc="desc")),
        (
            '* "payee payee" "desc desc"',
            Narration(Payee("payee payee"), "desc desc", "*"),
        ),
        (
            '2021-09-24 ! "payee payee" "desc desc"',
            Narration(Payee("payee payee"), "desc desc", "!", date(2021, 9, 24)),
        )
    )
    for tc in testcases:
        got = parser.parse(tc[0], lexer=lexer.clone())
        assert got == tc[1]
        parser.restart()


def test_transaction(parser, lexer, today):
    s = '! @abc "def ghi" -100 USD from + 300 CNY from2 > USD to1 + CNY to2'
    exp = Transaction(
        narration=Narration(
            Payee("abc"),
            "def ghi",
            "!",
            today,
        ),
        postings=[
            Posting("from", Decimal(-100), "USD"),
            Posting("from2", Decimal(300), "CNY"),
            Posting("to1", Decimal(100), "USD"),
            Posting("to2", Decimal(-300), "CNY"),
        ]
    )
    trx = parser.parse(s, lexer=lexer)
    assert trx == exp


def test_pipe_transaction(parser, lexer):
    s = '2021-09-24 麦当劳 汉堡\n| from 24 | to1 -18\n| to2 -6'
    exp = Transaction(
        narration=Narration(
            Payee("麦当劳"),
            "汉堡",
            "*",
            date(2021, 9, 24),
        ),
        postings=[
            Posting("from", Decimal(24), "CNY"),
            Posting("to1", Decimal(-18), "CNY"),
            Posting("to2", Decimal(-6), "CNY"),
        ]
    )
    trx = parser.parse(s, lexer=lexer)
    assert trx == exp


def test_comment(parser, lexer):
    inputs = (
        ";      hi hi hi hello",
        "//\thi hi hi hello",
    )
    exp = Comment("hi hi hi hello")
    for i in inputs:
        got = parser.parse(i, lexer=lexer.clone())
        assert got == exp
        parser.restart()


def test_open_and_close(parser, lexer):
    testcases = (
        ("open Assets:Bank", UnaryEntry("open", "Assets:Bank")),
        ("2021-01-01 close Assets:Bank",
         UnaryEntry("close", "Assets:Bank", date(2021, 1, 1))),
    )
    for tc in testcases:
        cmt = parser.parse(tc[0], lexer=lexer.clone())
        assert cmt == tc[1]
        parser.restart()


def test_commodity(parser, lexer):
    testcases = (
        ("commodity CAD", UnaryEntry("commodity", "CAD")),
        ("1867-01-01 commodity CAD", UnaryEntry("commodity", "CAD", date(1867, 1, 1))),
    )
    for tc in testcases:
        res = parser.parse(tc[0], lexer=lexer.clone())
        assert res == tc[1]
        parser.restart()


def test_option(parser, lexer):
    testcases = (
        ("option title Example Costflow file",
         Option("title", "Example Costflow file")),
        ("option operating_currency CNY",
         Option("operating_currency", "CNY")),
        ('option "conversion_currency" "NOTHING"',
         Option("conversion_currency", "NOTHING")),
    )
    for tc in testcases:
        res = parser.parse(tc[0], lexer=lexer.clone())
        assert res == tc[1]
        parser.restart()


def test_event_and_note(parser, lexer):
    testcases = (
        ('2017-01-02 event "location" "Paris, France"',
         KVEntry("event", "location", "Paris, France", date(2017, 1, 2))),
        ("event location Paris, France",
         KVEntry("event", "location", "Paris, France")),
        ("2019-07-01 note bofa Called about fraudulent card.",
         KVEntry("note", "bofa", "Called about fraudulent card.", date(2019, 7, 1))),
        ("note bofa Called about fraudulent card.",
         KVEntry("note", "bofa", "Called about fraudulent card.")),
    )
    for tc in testcases:
        res = parser.parse(tc[0], lexer=lexer.clone())
        assert res == tc[1]
        parser.restart()


def test_balance(parser, lexer):
    testcases = (
        ('2017-01-01 balance Assets:BofA 360 USD', Balance("Assets:BofA", Decimal(360), "USD", date(2017, 1, 1))),
        ("balance BofA 1024", Balance("BofA", Decimal(1024), "CNY")),
    )
    for tc in testcases:
        res = parser.parse(tc[0], lexer=lexer.clone())
        assert res == tc[1]
        parser.restart()


def test_pad(parser, lexer):
    testcases = (
        ('2017-01-01 pad bofa eob', Pad("bofa", "eob", date(2017, 1, 1))),
        ('pad bofa eob', Pad("bofa", "eob")),
    )
    for tc in testcases:
        res = parser.parse(tc[0], lexer=lexer.clone())
        assert res == tc[1]
        parser.restart()
