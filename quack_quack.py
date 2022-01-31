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
         | ESCAPED_STRING -> str
         
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

#Queue for reversing the order
call_q = []
#Number of return (length of field dic)
num_ret = 0
#List of Types
types = ["Bool","Int","Nothing","Obj","String"]
#Global tables
field_dic = {}
arg_dic = {}
local_dic = {}
pop_list = ["print"]
logics = ["plus", "sub", "mult", "div"]

@v_args(inline=True)    # Affects the signatures of the methods
class Set(visitors.Visitor_Recursive):

    def __default__(self, tree):
        if tree.data == "assignment":
            key, value = tree.children[0].children[0], tree.children[1].children[0]
            local_dic[key] = value

    def exec(self, tree):
        if len(field_dic) > 0:
            num_ret = len(field_dic)
            call = ".field "
            for count,field in enumerate(field_dic):
                if count == 0:
                    call += field[0]
                else:
                    call += "," + field[0]
            call_q.append(call)
        elif len(arg_dic) > 0:
            call = ".args "
            for count,field in enumerate(arg_dic):
                if count == 0:
                    call += field[0]
                else:
                    call += "," + field[0]
            call_q.append(call)
        elif len(local_dic) > 0:
            call = ".local "
            for count,field in enumerate(local_dic):
                if count == 0:
                    call += field
                else:
                    call += "," + field
            call_q.append(call)


class Convert(visitors.Visitor_Recursive):

    def __default__(self, tree):
        if tree.data == "const" :
            self.cur_type = "Int"
        if tree.data == "str" :
            self.cur_type = "String"
            tree.data = "const"

        if tree.data == "load" :
            if tree.children[0] in field_dic:
                self.cur_type = field_dic[tree.children[0]]
            elif tree.children[0] in arg_dic:
                self.cur_type = arg_dic[tree.children[0]]
            elif tree.children[0] in local_dic:
                self.cur_type = local_dic[tree.children[0]]

        elif tree.data == "statement":
            tree.data = self.cur_type

        elif tree.data == "assignment":
            local_dic[tree.children[0].children[0]] = tree.children[1].children[0]
            tree.children[0].data = "store"



class Store(visitors.Visitor_Recursive):
    def __init__(self):
        self.que = []

    def __default__(self, tree):
        def traverse(tr):
            for subtree in tr.iter_subtrees_topdown():
                if subtree.data == "load" or  subtree.data == "store" or subtree.data == "const":
                    call = subtree.data + " " + subtree.children[0]
                    self.que.append(call)
                elif subtree.data == "neg":
                    self.que.append("call Int:sub")
                    self.que.append("const 0")
                elif subtree.data in logics:
                    call = "call " + tr.data + ":" + subtree.data
                    self.que.append(call)
                elif subtree.data == "method":
                    new_call = "call " + tr.data + ":" + subtree.children[0]
                    if subtree.children[0] in pop_list:
                        subtree.children[0] = new_call + "\npop"
                    else:
                        subtree.children[0] = new_call
                    self.que.append(new_call)

            while len(self.que):
                call_q.append(self.que.pop())

        if tree.data == "method":
            temp_obj = tree.children[0]
            tree.children[0] = tree.children[1]
            tree.children[1] = temp_obj

        elif tree.data in types:
            traverse(tree)


def main():
    quack_parser = Lark(quack_grammar, parser='lalr')
    quack = quack_parser.parse

    code = sys.stdin.read()

    call_q.append(".class Quack:Obj")
    call_q.append(".method $constructor")

    sample = quack(code)
    Set().visit(sample)
    Convert().visit(sample)
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