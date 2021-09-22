from datetime import date, datetime
from dataclasses import dataclass
from decimal import Decimal
from collections import defaultdict


@dataclass
class Payee:
    payee: str

    def __str__(self):
        return self.payee


@dataclass
class Narration:
    payee: Payee
    desc: str
    type_: str = "*"
    date_: date = datetime.today().date()


DEFAULT_CURRENCY = "CNY"


@dataclass
class Posting:
    account: str
    amount: Decimal = None
    currency: str = None


class Transaction:
    def __init__(self, narration):
        self.narration = narration
        self.postings = []

    def push(self, posting):
        self.postings.append(posting)

    def build(self):
        "Fill empty currency and amount"
        currency = None
        empty = []
        for posting in self.postings:
            if posting.currency is None:
                empty.append(posting)
            elif currency is None:
                currency = posting.currency
        if currency is None:
            currency = DEFAULT_CURRENCY
        for posting in empty:
            posting.currency = currency

        # Rebalance amount by currency
        amounts = defaultdict(Decimal)
        empty_amounts = defaultdict(list)
        for posting in self.postings:
            cur = posting.currency
            if posting.amount is None:
                empty_amounts[cur].append(posting)
            else:
                amounts[cur] -= posting.amount

        for cur, postings in empty_amounts.items():
            avg_amount = amounts[cur] / len(postings)
            for posting in postings:
                posting.amount = avg_amount

    def render(self):
        date = self.narration.date_
        if not date:
            date = datetime.today().date()

        lines = [f'{date} {self.narration.type_} "{self.narration.payee}" "{self.narration.desc}"']
        for posting in self.postings:
            # TODO: account finding
            lines.append("\t{}\t{:.2f} {}".format(posting.account, posting.amount, posting.currency))
        return "\n".join(lines)
