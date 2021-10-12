from datetime import datetime
from decimal import Decimal
import pytest
from costflow import Costflow
from costflow.config import Config
from costflow.definitions import (
    Comment, Transaction, Narration, Posting, Payee,
)


@pytest.fixture
def today():
    return datetime.today().date()


def test_formula():
    testcases = [
        ("btv", "{{ pre }} bofa > visa", ["123"], "123 bofa > visa"),
        ("☕️", "@{{ pre }} ☕️ {{ amount*2 }} visa > coffee", ["10.24", "Leplay's"],
         "@Leplay's ☕️ 20.48 visa > coffee"),
        ("loop", "loop", [], "loop"),
        ("tb", "tmr balance {{pre}}", ["123.45", "CNY"], "tmr balance 123.45 CNY"),
    ]
    formulas = {t[0]: t[1] for t in testcases}

    conf = Config(formulas=formulas)
    costflow = Costflow(conf)

    for tc in testcases:
        exp = costflow.compile_template(tc[1], tc[2])
    assert exp == tc[3]


def test_parse(today):
    formulas = {
        "valid": "{{ pre }} bofa > visa",
        "invalid": "abcdefghijk"
    }
    conf = Config(formulas=formulas)
    costflow = Costflow(conf)
    trx = Transaction(
        narration=Narration(payee=Payee("payee"), desc="",
                            type_="*", date_=today),
        postings=[
            Posting(account="bofa", amount=Decimal(100), currency="CNY"),
            Posting(account="visa", amount=Decimal(-100), currency="CNY"),
        ]
    )
    testcases = [
        # Normal input
        ("@payee 100 bofa > visa", trx),
        # Formula directive
        ("f valid @payee 100", trx),
        # Formula fallback
        ("valid @payee 100", trx),
        # Comment fallback
        ("f invalid abcdefg", Comment("f invalid abcdefg")),
    ]

    for tc in testcases:
        inputs, exp = tc
        got = costflow.parse(inputs)
        assert got == exp
