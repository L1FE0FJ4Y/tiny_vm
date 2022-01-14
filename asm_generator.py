"""
Lark Parser Generator
================

REPL calculator shows how to write a basic calculator with variables.
"""
from lark import Lark, Transformer, v_args

calc_grammar = """
    ?start: sum             -> ret
          | NAME "=" sum    -> assign_var

    ?sum: product
        | sum "+" product   -> add
        | sum "-" product   -> sub

    ?product: atom
        | product "*" atom  -> mult
        | product "/" atom  -> div

    ?atom: NUMBER           -> number
         | "-" NUMBER       -> neg
         | NAME             -> var
         | "(" sum ")"
    
    %import common.CNAME -> NAME
    %import common.NUMBER
    %import common.WS_INLINE

    %ignore WS_INLINE
"""

@v_args(inline=True)    # Affects the signatures of the methods
class AsmTree(Transformer):

    def __init__(self):
        self.vars = {}
        self.instr = []

    def assign_var(self, name, value):
        self.vars[name] = value
        return value

    def var(self, name):
        try:
            return self.vars[name]
        except KeyError:
            raise Exception("Variable not found: %s" % name)

    def ret(self, x):
        return self.instr

    def add(self, left, right):
        self.instr.append("call Int:plus\n")

    def sub(self, left, right):
        self.instr.append("call Int:sub\n")

    def mult(self, left, right):
        self.instr.append("call Int:mult\n")

    def div(self, left, right):
        self.instr.append("call Int:div\n")

    def number(self, x):
        self.instr.append("const " + x + "\n")

    def neg(self, right):
        self.instr.append("const " + right + "\nconst 0\n")
        self.instr.append("call Int:sub\n")


def main():
    f = open("./unit_tests/sample.asm", "w")
    f.write(".class Sample:Obj\n\n.method $constructor\n")

    calc_parser = Lark(calc_grammar, parser='lalr', transformer=AsmTree())
    calc = calc_parser.parse
    s = input('> ')

    instr_set = calc(s)
    while instr_set:
        f.write(instr_set.pop(0))

    f.write("call Int:print\npop\nreturn 0")
    f.close()


if __name__ == '__main__':
    main()