from datetime import datetime, date
from decimal import Decimal
import pytest
from costflow.definitions import (
    Comment, Narration, Transaction, Posting, Balance,
    Pad, Option, KVEntry, UnaryEntry,
)


@pytest.fixture
def today():
    return datetime.today().date()


def test_transaction(today):
    testcases = (
        (
            # Normal transaction
            Transaction(
                narration=Narration(
                    "payee",
                    "desc",
                    "*",
                    date(2021, 1, 1)
                ),
                postings=[
                    Posting("Assets:Bank1", Decimal(10), "CNY"),
                    Posting("Assets:Bank2", Decimal(-10), "CNY"),
                ]
            ),
            '''\
2021-01-01 * "payee" "desc"
\tAssets:Bank1\t10.00 CNY
\tAssets:Bank2\t-10.00 CNY'''
        ),
        (
            # Auto date, fill amount, default currency
            Transaction(
                narration=Narration(
                    "",
                    "desc",
                ),
                postings=[
                    Posting("Assets:Bank1", Decimal(10)),
                    Posting("Assets:Bank2"),
                    Posting("Assets:Bank3"),
                ]
            ),
            f'''\
{today} * "" "desc"
\tAssets:Bank1\t10.00 CNY
\tAssets:Bank2\t-5.00 CNY
\tAssets:Bank3\t-5.00 CNY''',
        ),
        (
            # Auto amount, fill amount, multiple currency
            Transaction(
                narration=Narration(
                    "payee",
                    "",
                    "!",
                    date(2019, 1, 1),
                ),
                postings=[
                    Posting("Assets:USBank1", Decimal(10), "USD"),
                    Posting("Assets:CNBank2", Decimal(5), "CNY"),
                    Posting("Assets:USBank3", Decimal(2)),
                    Posting("Assets:CNBank4", currency="CNY"),
                ]
            ),
            '''\
2019-01-01 ! "payee" ""
\tAssets:USBank1\t10.00 USD
\tAssets:CNBank2\t5.00 CNY
\tAssets:USBank3\t2.00 USD
\tAssets:CNBank4\t-5.00 CNY'''
        ),
    )
    for tc in testcases:
        trx, exp = tc[0], tc[1]
        trx.build()
        got = trx.render()
        assert exp == got


def test_comment():
    testcases = (
        (Comment("hello beancount"), "; hello beancount"),
    )
    for tc in testcases:
        assert tc[0].render() == tc[1]


def test_unary_entry(today):
    testcases = (
        (UnaryEntry("open", "Assets:Bank"), f"{today} open Assets:Bank"),
        (UnaryEntry("close", "Assets:Bank", date(2021, 1, 1)),
         "2021-01-01 close Assets:Bank"),
        (UnaryEntry("commodity", "CAD"),
         f"{today} commodity CAD"),
        (UnaryEntry("commodity", "CAD", date(1867, 1, 1)),
         "1867-01-01 commodity CAD"),
    )
    for tc in testcases:
        assert tc[0].render() == tc[1]


def test_option():
    testcases = (
        (Option("title", "Example Costflow file"),
         'option "title" "Example Costflow file"'),
        (Option("operating_currency", "CNY"),
         'option "operating_currency" "CNY"'),
        (Option("conversion_currency", "NOTHING"), 'option "conversion_currency" "NOTHING"'),
    )
    for tc in testcases:
        assert tc[0].render() == tc[1]


def test_event_and_note(today):
    today = datetime.today().date()
    testcases = (
        (KVEntry("event", "location", "Paris, France", date(2017, 1, 2)),
         '2017-01-02 event "location" "Paris, France"'),
        (KVEntry("event", "location", "Paris, France"),
         f'{today} event "location" "Paris, France"'),
        (KVEntry("note", "bofa", "Called about fraudulent card.", date(2019, 7, 1)),
         '2019-07-01 note bofa "Called about fraudulent card."'),
        (KVEntry("note", "bofa", "Called about fraudulent card."),
         f'{today} note bofa "Called about fraudulent card."'),
    )
    for tc in testcases:
        assert tc[0].render() == tc[1]


def test_balance(today):
    testcases = (
        (Balance("Assets:BofA", Decimal(360), "USD", date(2017, 1, 1)),
         "2017-01-01 balance Assets:BofA 360 USD"),
        (Balance("Assets:BofA", Decimal(360)),
         f"{today} balance Assets:BofA 360 CNY"),
    )
    for tc in testcases:
        assert tc[0].render() == tc[1]


def test_pad(today):
    testcases = (
        (Pad("bofa", "eob", date(2017, 1, 1)),
         "2017-01-01 pad bofa eob"),
        (Pad("bofa", "eob"),
         f"{today} pad bofa eob"),
    )
    for tc in testcases:
        assert tc[0].render() == tc[1]
