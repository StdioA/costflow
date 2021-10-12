from ply import lex, yacc
from . import rules, utils, definitions, config
from jinja2 import Template


class Costflow:
    def __init__(self, conf=None):
        if conf is not None:
            config.config = conf

        self.parser = yacc.yacc(module=rules)
        self.lexer = lex.lex(module=rules)

    def compile_template(self, formula, inputs):
        variables = utils.fetch_variables(formula)
        amount, pre = "", ""
        if "amount" in variables:
            amount = inputs[0]
            inputs = inputs[1:]
        if "pre" in variables:
            pre = " ".join(inputs)
        return Template(formula).render(pre=pre, amount=amount)

    def _process_template(self, segments):
        formula_name, *variables = segments
        formula = config.config.get_formula(formula_name)
        output = self.compile_template(formula, variables)
        if output:
            return self.parse_raw(output)

    def parse_raw(self, inputs):
        try:
            return self.parser.parse(inputs, lexer=self.lexer.clone())
        except definitions.CostflowSyntaxError:
            pass
        finally:
            self.parser.restart()

    def parse(self, inputs):
        result = None
        # Try to render template
        segments = inputs.split()
        if segments[0] == "f" and len(segments) > 1:
            result = self._process_template(segments[1:])
            if result is not None:
                return result

        # Parse original string
        result = self.parse_raw(inputs)
        if result is not None:
            return result

        # Fallback to formula
        result = self._process_template(segments)
        if result is not None:
            return result

        # Fallback to comment
        return definitions.Comment(inputs)
