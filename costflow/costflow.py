from ply import lex, yacc
from . import rules


class Costflow:
    def __init__(self, config):
        self.config = config
        self.parser = yacc.yacc(module=rules)
        self.lexer = lex.lex(module=rules)

    def parse(self, inputs):
        # TODO: Fallback rules for formula & comments
        return self.parser.parse(inputs, lexer=self.lexer.clone())
