from datetime import date, datetime
from dataclasses import dataclass
from decimal import Decimal
from collections import defaultdict
from abc import ABCMeta, abstractmethod
from utils import check_account


class Entry(metaclass=ABCMeta):
    @abstractmethod
    def render(self):
        pass

    def fill_date(self):
        if self.date_ is None:
            self.date_ = datetime.today().date()


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


class Transaction(Entry):
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


@dataclass
class Comment(Entry):
    content: str

    def build(self):
        pass

    def render(self):
        return f";{self.content}"


@dataclass
class UnaryEntry(Entry):
    directive: str
    content: str
    date_: date = None

    def build(self):
        if self.directive in ("open", "close"):
            check_account(self.content)

    def render(self):
        self.fill_date()
        return f"{self.date_} {self.directive} {self.content}"


@dataclass
class Option(Entry):
    key: str
    value: str

    def render(self):
        return f'option "{self.key}" "{self.value}"'


@dataclass
class KVEntry(Entry):
    directive: str
    key: str
    value: str
    date_: date = None

    def build(self):
        # TODO: account finding on note directive
        pass

    def render(self):
        self.fill_date()

        # the key in note directive stands for account
        key = self.key
        if self.directive != "note":
            key = f'"{key}"'
        return f'{self.date_} {self.directive} {key} "{self.value}"'


@dataclass
class Balance(Entry):
    account: str
    amount: Decimal
    currency: str = DEFAULT_CURRENCY
    date_: date = None

    def build(self):
        # TODO: account finding on account directive
        pass

    def render(self):
        self.fill_date()
        return f'{self.date_} balance {self.account} {self.amount} {self.currency}'


@dataclass
class Pad(Entry):
    account: str
    to_account: str
    date_: date = None

    def build(self):
        # TODO: account finding
        pass

    def render(self):
        self.fill_date()
        return f'{self.date_} pad {self.account} {self.to_account}'
