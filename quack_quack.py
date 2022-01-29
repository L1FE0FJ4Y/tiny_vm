"""
Lark Parser Generator
================

REPL calculator shows how to write a basic calculator with variables.
"""
from lark import Lark, Transformer, v_args, visitors
import sys
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

quack_grammar = """
    ?start: program -> exec
    
    ?program: statement*
    
    statement: r_exp ";"
        | assignment ";"
        | method ";"

    assignment: l_exp ":" type "=" r_exp
        
    method: r_exp "." NAME "(" ")"

    type: NAME
    
    ?r_exp: calc
        | method
    
    l_exp: NAME -> load
         | ESCAPED_STRING -> const
         
    ?calc: product
        | calc "+" product   -> plus
        | calc "-" product   -> sub

    ?product: atom
        | product "*" atom  -> mult
        | product "/" atom  -> div

    ?atom: NUMBER           -> const
         | "-" atom         -> neg
         | l_exp
         | "(" calc ")"
    
    %import common.ESCAPED_STRING
    %import common.CNAME -> NAME
    %import common.NUMBER
    %import common.WS

    %ignore WS
"""

call_q = []
num_ret = 0

@v_args(inline=True)    # Affects the signatures of the methods
class Set(visitors.Visitor_Recursive):

    def __init__(self):
        self.field_dic = {}
        self.arg_dic = {}
        self.local_dic = {}

    def __default__(self, tree):
        if tree.data == "assignment":
            key, value = tree.children[0].children[0], tree.children[1].children[0]
            self.local_dic[key] = value

    def exec(self, tree):
        if len(self.field_dic) > 0:
            num_ret = len(self.field_dic)
            call = ".field "
            for count,field in enumerate(self.field_dic):
                if count == 0:
                    call += field[0]
                else:
                    call += "," + field[0]
            call_q.append(call)
        elif len(self.arg_dic) > 0:
            call = ".args "
            for count,field in enumerate(self.arg_dic):
                if count == 0:
                    call += field[0]
                else:
                    call += "," + field[0]
            call_q.append(call)
        elif len(self.local_dic) > 0:
            call = ".local "
            for count,field in enumerate(self.local_dic):
                if count == 0:
                    call += field
                else:
                    call += "," + field
            call_q.append(call)


class Convert(visitors.Visitor_Recursive):
    def __init__(self):
        self.field_dic = {}
        self.arg_dic = {}
        self.local_dic = {}

    def __default__(self, tree):
        if tree.data == "const" :
            self.cur_type = "Int"

        if tree.data == "load" :
            if tree.children[0] in self.field_dic:
                self.cur_type = self.field_dic[tree.children[0]]
            elif tree.children[0] in self.arg_dic:
                self.cur_type = self.arg_dic[tree.children[0]]
            elif tree.children[0] in self.local_dic:
                self.cur_type = self.local_dic[tree.children[0]]

        elif tree.data == "plus":
            tree.data = "call " + self.cur_type + ":" + tree.data

        elif tree.data == "sub":
            tree.data = "call " + self.cur_type + ":" + tree.data

        elif tree.data == "mult":
            tree.data = "call " + self.cur_type + ":" + tree.data

        elif tree.data == "div":
            tree.data = "call " + self.cur_type + ":" + tree.data

        elif tree.data == "assignment":
            self.local_dic[tree.children[0].children[0]] = tree.children[1].children[0]
            tree.children[0].data = "store"
            self.cur_type = tree.children[1].children[0]

        elif tree.data == "method":
            tree.children[1] = "call " + self.cur_type + ":" + tree.children[1] + "\npop"


class Store(visitors.Visitor_Recursive):
    def __init__(self):
        self.que = []

    def __default__(self, tree):
        def traverse():
            for subtree in tree.iter_subtrees_topdown():
                if subtree.data == "load" or  subtree.data == "store" or subtree.data == "const":
                    call = subtree.data + " " + subtree.children[0]
                    self.que.append(call)
                elif subtree.data == "neg":
                    self.que.append("call Int:sub")
                    self.que.append("const 0")
                elif "call" in subtree.data:
                    call = subtree.data
                    self.que.append(call)
            while len(self.que):
                call_q.append(self.que.pop())

        if tree.data == "assignment":
            traverse()
        elif tree.data == "method":
            self.que.append(tree.children[1])
            traverse()



def main():
    quack_parser = Lark(quack_grammar, parser='lalr')
    quack = quack_parser.parse

    code = sys.stdin.read()

    call_q.append(".class Quack:Obj")
    call_q.append(".method $constructor")

    sample = quack(code)
    Set().visit(sample)
    sample = Convert().visit(sample)
    Store().visit(sample)

    f = open("./Quack.asm", "w")
    while call_q:
        f.write(call_q.pop(0))
        f.write("\n")

    if num_ret == 0:
        f.write("const nothing\n")
    end_clause = "return " + str(num_ret)
    f.write(end_clause)
    f.close()

    os.system('python assemble.py Quack.asm OBJ/Quack.json')

if __name__ == '__main__':
    if len(sys.argv) < 1:
        print("Need more argument")
        sys.exit(1)
    main()
    os.system('./bin/tiny_vm Quack')