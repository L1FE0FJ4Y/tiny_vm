"""
Lark Parser Generator
================

REPL calculator shows how to write a basic calculator with variables.
"""
from lark import Lark, Transformer, v_args
import os

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
         | "-" atom         -> neg
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
        self.neg_flag = 0
        self.eq_flag = 0
        self.num_flag = 0

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
        self.instr.append("const 0\n")
        self.instr.append("const 1\n")
        self.instr.append("call Int:sub\n")
        self.instr.append("call Int:mult\n")


def main():
    f = open("./unit_tests/sample.asm", "w")
    f.write(".class Sample:Obj\n\n.method $constructor\n")

    calc_parser = Lark(calc_grammar, parser='lalr', transformer=AsmTree())
    calc = calc_parser.parse
    s = input('> ')

    instr_set = calc(s)
    while instr_set:
        f.write(instr_set.pop(0))

    newline_clause = 'const "\\n"\ncall  String:print\npop\n'
    eq_clause = 'const "' + s + ' = "\ncall String:print\npop\n'
    end_clause = eq_clause + 'call Int:print\npop\n'+newline_clause+'const "Operation Done"\ncall String:print\npop\nreturn 0'
    f.write(end_clause)
    f.close()


if __name__ == '__main__':
    main()
    os.system('python assemble.py unit_tests/sample.asm sample.json')