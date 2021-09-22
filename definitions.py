from datetime import date, datetime
from dataclasses import dataclass
from decimal import Decimal


class Payee:
    def __init__(self, s):
        self.payee = s
    
    def __str__(self):
        return self.payee

    def __repr__(self):
        return f"@{self.payee}"

@dataclass
class Narration:
    payee: Payee
    desc: str
    type_: str = "*"
    date: date = datetime.today().date()


@dataclass
class Posting:
    account: str
    amount: Decimal
    currency: str = "CNY"


class Transaction:
    def __init__(self, narration):
        self.narration = narration
        self.postings = []

    def push(self, posting):
        self.postings.append(posting)

    @property
    def amount_left(self):
        amount = Decimal(0)
        for posting in self.postings:
            amount -= posting.amount
        return amount
    
    def render(self):
        date = self.narration.date
        if not date:
            date = datetime.today().date()

        lines = [f'{date} {self.narration.type_} "{self.narration.payee}" "{self.narration.desc}"']
        for posting in self.postings:
            # TODO: account finding
            # TODO: commodity
            lines.append("\t{}\t{:.2f} {}".format(posting.account, posting.amount, posting.currency))
        return "\n".join(lines)