from dataclasses import dataclass, field


@dataclass
class Config:
    default_currency: str = "CNY"
    formulas: dict = field(default_factory=dict)

    def get_formula(self, name):
        return self.formulas.get(name, "")

    # TODO: Beancount loader for default currency


# Global store
config = Config()
