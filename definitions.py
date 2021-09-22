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

    @property
    def amount_left(self):
        amount = Decimal(0)
        for posting in self.postings:
            amount -= posting.amount
        return amount
    
    def rebalance(self):
        amount = Decimal(0)
        empty_amounts = []
        # TODO: Check currency
        for posting in self.postings:
            if posting.amount is None:
                empty_amounts.append(posting)
            else:
                amount -= posting.amount
        if not empty_amounts:
            return
        avg_amount = amount / len(empty_amounts)
        for amount in empty_amounts:
            amount.amount = avg_amount
        
    def build(self):
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
