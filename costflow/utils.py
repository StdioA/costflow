from jinja2 import Environment, meta


def fetch_variables(tmpl):
    env = Environment()
    ast = env.parse(tmpl)
    return meta.find_undeclared_variables(ast)



def check_account(account):
    # TODO: Check account name (utf-8 validation)
    pass
