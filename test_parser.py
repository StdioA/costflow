import pytest
from datetime import datetime
import costflow
from ply import lex, yacc
from definitions import Transaction, Comment, UnaryEntry


@pytest.fixture
def parser():
    return yacc.yacc(module=costflow)


@pytest.fixture
def lexer():
    return lex.lex(module=costflow)


def test_transaction(parser, lexer):
    s = '! @abc "def ghi" -100 USD from + 300 CNY from2 > USD to1 + CNY to2'
    exp = '''\
2021-09-23 ! "abc" "def ghi"
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
