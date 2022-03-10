"""
Lark Parser Generator
================

REPL calculator shows how to write a basic calculator with variables.
"""
from lark import Lark, Transformer, v_args, visitors
import sys, os
import json
from typing import List, Callable
import logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


JUMP_COUNT = 0
def new_label(prefix: str) -> str:
    global JUMP_COUNT
    JUMP_COUNT += 1
    return f"{prefix}_{JUMP_COUNT}"

def ignore(node: "ASTNode", visit_state, variables):
    log.debug(f"No visitor action at {node.__class__.__name__} node")
    return

def flatten(m: list):
    """Flatten nested lists into a single level of list"""
    flat = []
    for item in m:
        if isinstance(item, list):
            flat += flatten(item)
        else:
            flat.append(item)
    return flat


class ASTNode:
    """Abstract base class"""
    def __init__(self):
        self.children = []    # Internal nodes should set this to list of child nodes
        self.type

    def initialization(self, visit_state: dict):
        if self.children:
            for c in flatten([self.children]):
                c.initialization(visit_state)
        else: ignore(self, visit_state)

    def type_check(self, visit_state: dict):
        if self.children:
            for c in flatten([self.children]):
                c.initialization(visit_state)
        else: ignore(self, visit_state)

    def r_eval(self, visit_state: dict) -> List[str]:
        """Evaluate for value"""
        #raise NotImplementedError(f"r_eval not implemented for node type {self.__class__.__name__}")
        raise NotImplementedError(f"r_eval not implemented for node type {self.__class__.__name__}")

    def c_eval(self, true_branch: str, false_branch: str) -> List[str]:
        raise NotImplementedError(f"c_eval not implemented for node type {self.__class__.__name__}")


class ProgramNode(ASTNode):
    '''program : [(classes)* (statement)*]'''
    def __init__(self, classes: List[ASTNode] = [], methods: List[ASTNode] = [], stmt_block: List[ASTNode] = []):
        self.classes = classes
        main_class = ClassNode("$Main", [], "Obj", stmt_block, methods)
        self.classes.append(main_class)
        self.children = [classes, methods, stmt_block]

    def __str__(self) -> str:
        return "\n".join([str(c) for c in self.classes])


class ClassNode(ASTNode):
    '''classes : class_sig class_body'''
    def __init__(self, name: str, formals: List[ASTNode],
                 super_class: str,
                 block: List[ASTNode],
                 methods: List[ASTNode]):
        self.name = name
        self.formals = formals
        self.super_class = super_class
        self.methods = methods
        self.constructor = MethodNode("$constructor", formals, name, block)
        self.children = [methods, self.constructor]

    def __str__(self):
        ret = f"\n.class {self.name}:{self.super_class}\n"
        formals_str = ", ".join([str(fm) for fm in flatten([self.formals])])
        if formals_str:
            ret += f".field {formals_str}\n"
        methods_str = "\n".join([f"{method}" for method in flatten([self.methods])])
        ret += f"{methods_str}\n\n{self.constructor}"
        return ret

    def initialization(self, visit_state: List):
        """Create class entry in symbol table (as a preorder visit)"""
        if self.name in visit_state:
            raise Exception(f"Shadowing class {self.name} is not permitted")
        visit_state[self.name] = {
            "super": self.super_class,
            "fields": { f"{fm.var_type}" for fm in flatten([self.formals])},
            "methods": {}
        }
        visit_state["current_class"] = str(self.name)
        visit_state["fields"] = set()
        for fm in flatten([self.formals]):
            visit_state["fields"].add(str(fm))
        if self.children:
            for c in flatten(self.children):
                c.initialization(visit_state)


###FIX RETURN
class MethodNode(ASTNode):
    def __init__(self, name: str, formals: List[ASTNode],
                 returns: str, body: List[ASTNode]):
        self.name = name
        self.formals = formals
        self.returns = returns
        self.body = body
        self.variables = {}
        self.children = [formals, body]

    def __str__(self):
        ret = f".method {self.name}\n"
        if self.formals:
            formals_str = ",".join([str(fm) for fm in flatten([self.formals])])
            ret += f".args {formals_str}\n"
        if self.variables:
            locals_str = ",".join([str(v) for v in self.variables])
            ret += f".local {locals_str}\n"
        if self.body:
            ret += "\n".join([str(b) for b in flatten([self.body])])
        f_size = len(flatten([self.formals]))
        if f_size:
            ret += f"\nreturn {f_size}"
        else:
            ret += f"\nconst nothing\nreturn {len(self.formals)}"
        return ret

    # Add this method to the symbol table
    def initialization(self, visit_state: List):
        visit_state["current_method"] = str(self.name)
        clazz = visit_state["current_class"]
        if self.name in visit_state[clazz]:
            raise Exception(f"Redeclaration of method {self.name} not permitted")
        visit_state[clazz]["methods"][str(self.name)] = { "params": { f"{fm.var_type}" for fm in flatten([self.formals])}, "ret": str(self.returns) }

        visit_state["def_init"] = set()
        classField = visit_state["fields"].copy()
        for fm in flatten([self.formals]):
            visit_state["fields"].add(str(fm))

        if self.children:
            for c in flatten(self.children):
                c.initialization(visit_state)
        visit_state["fields"] = classField
        self.variables = visit_state["def_init"]
        visit_state["def_init"] = set()


class FormalNode(ASTNode):
    def __init__(self, var_name: ASTNode, var_type: ASTNode):
        self.var_name = var_name
        self.var_type = var_type
        self.children = [var_name, var_type]

    def __str__(self):
        return f"{self.var_name}"

#type
class ReturnNode(ASTNode):
    """return : "return" [r_exp]"""
    def __init__(self, ret: List[ASTNode]):
        self.ret = ret
        self.children = ret

    def __str__(self):
        ret = "\n".join([str(r) for r in self.ret])
        return ret


class AsmtNode(ASTNode):
    """assignment : l_exp [":" ident] "=" r_exp"""
    def __init__(self, left: ASTNode, ident: ASTNode, right: ASTNode):
        self.left = left
        self.type = ident
        self.right = right
        self.children = [right, left]

    def __str__(self):
        ret = "\n".join([str(re) for re in self.children])
        return ret

    def initialization(self, visit_state: dict):
        self.right.initialization(visit_state)
        var = self.left.initialization(visit_state)
        if var not in visit_state["fields"]:
            visit_state["def_init"].add(var)


class WhileNode(ASTNode):
    """while_stmt : "while" condition stmt_block"""
    """if condition stmt_block [otherwise*]"""
    def __init__(self,
                 cond: ASTNode,
                 whilepart: ASTNode):
        self.cond = cond
        self.whilepart = whilepart
        self.children = [cond, whilepart]

    def __str__(self):
        cond_label = new_label("cond")
        loop_label = new_label("loop")
        endloop_label = new_label("endloop")
        iftest = "\n".join([str(it) for it in flatten(self.cond.c_eval(loop_label, endloop_label))])
        ret = f'''{cond_label}:\n{iftest}\n{loop_label}:\n'''
        ret += '\n'.join([str(t) for t in flatten([self.whilepart])])
        return ret + f"\njump {cond_label}\n{endloop_label}:"

    def initialization(self, visit_state: dict):
        original = visit_state["def_init"].copy()
        self.cond.initialization(visit_state)
        for w in self.whilepart:
            w.initialization(visit_state)
        visit_state["def_init"] = original


class IfNode(ASTNode):
    """if condition stmt_block [otherwise*]"""
    def __init__(self,
                 cond: ASTNode,
                 thenpart: ASTNode,
                 elsepart: List[ASTNode]):
        self.cond = cond
        self.thenpart = thenpart
        self.elsepart = elsepart
        self.children = [cond, thenpart, elsepart]

    def __str__(self):
        then_label = new_label("then")
        else_label = new_label("else")
        endif_label = new_label("endif")
        iftest = "\n".join([str(it) for it in flatten(self.cond.c_eval(then_label, else_label))])
        retStr =  f"{iftest}\n{then_label}:\n"
        retStr += '\n'.join([str(t) for t in flatten([self.thenpart])])
        retStr += f"\njump {endif_label}\n"
        if self.elsepart:
            retStr += f"{else_label}:\n"
            retStr += '\n'.join([str(e) for e in flatten([self.elsepart])])
        return retStr + f"\n{endif_label}:"


    def initialization(self, visit_state: dict):
        for c in flatten([self.cond]):
            c.initialization(visit_state)
        before = visit_state["def_init"].copy()
        for t in flatten([self.thenpart]):
            t.initialization(visit_state)
        init_if_true = visit_state["def_init"].copy()
        visit_state["def_init"] = before
        for e in flatten([self.elsepart]):
            e.initialization(visit_state)
        init_if_false = visit_state["def_init"].copy()
        init_var = set()
        for var in init_if_true:
            if var in init_if_false:
                init_var.add(var)
        visit_state["def_init"] = init_var


class AndNode(ASTNode):
    """Boolean and, short circuit; can be evaluated for jump or for boolean value"""
    def __init__(self, left: ASTNode, right: ASTNode):
        self.left = left
        self.right = right
        self.children = [left, right]

    def c_eval(self, true_branch: str, false_branch: str) -> List[str]:
        """Use in a conditional branch"""
        continue_label = new_label("and")
        return ( self.left.c_eval(continue_label, false_branch)
                 + [continue_label + ":"]
                 + self.right.c_eval(true_branch, false_branch)
                 )


class OrNode(ASTNode):
    """Boolean or, short circuit; can be evaluated for jump or for boolean value"""

    def __init__(self, left: ASTNode, right: ASTNode):
        self.left = left
        self.right = right
        self.children = [left, right]

    def c_eval(self, true_branch: str, false_branch: str) -> List[str]:
        """Use in a conditional branch"""
        continue_label = new_label("or")
        return (self.left.c_eval(true_branch, continue_label)
                + [continue_label + ":"]
                + self.right.c_eval(true_branch, false_branch)
                )


class ComparisonNode(ASTNode):
    """
    Comparisons are the leaves of conditional branches
    and can also return boolean values
    """
    def __init__(self, comp_op: str, left: ASTNode, right: ASTNode):
        self.type = "Obj"
        self.comp_op = comp_op
        self.left = left
        self.right = right
        self.children = [right, left]

    def c_eval(self, true_branch: str, false_branch: str) -> List[str]:
        bool_code = self.children
        return bool_code + [f"call {self.type}:{self.comp_op}\njump_if {true_branch}", f"jump {false_branch}"]


class NotNode(ASTNode):
    """"not" r_exp -> not"""
    def __init__(self, right: List[ASTNode]):
        self.right = right
        self.children = right

    def c_eval(self, true_branch: str, false_branch: str) -> List[str]:
        return self.right.c_eval(false_branch, true_branch)


class NewNode(ASTNode):
    class MethodCallNode(ASTNode):
        '''r_exp "." ident "(" args* ")" ->method_call'''
    def __init__(self, ident: ASTNode, args: List[ASTNode]):
        self.ident = ident
        self.args = args
        self.children = [args, ident]

    def __str__(self):
        ret = f"new {self.ident}\ncall {self.ident}:$constructor"
        return ret

###IMPORTANT AND HARD TYPE CHECK
class MethodCallNode(ASTNode):
    '''r_exp "." ident "(" args* ")" -> method_call'''
    def __init__(self, ident: ASTNode, left: List[ASTNode], right: List[ASTNode]):
        self.type = "Obj"
        self.ident = ident
        self.left = left
        self.right = right
        self.children = [left, right]

    def __str__(self):
        ret = f"{self.left}\n"
        if self.right:
            ret += f"{self.right}\n"
        return ret + f"call {self.type}:{self.ident}"


class ArithNode(ASTNode):
    """Arithmetic operations"""
    def __init__(self, op: str, left: ASTNode, right: ASTNode):
        self.type = ''
        self.op = op
        self.left = left
        self.right = right
        self.children = [left, right]

    def __str__(self):
        return f"{self.right}\n{self.left}\ncall {self.type}:{self.op}"



class ArgsNode(ASTNode):
    """r_exp"""
    def __init__(self, right: ASTNode):
        self.right = right
        self.children = [right]

    def __str__(self):
        return str(self.right)


class NegateNode(ASTNode):
    """Arithmetic operations"""
    def __init__(self, exps: List[ASTNode]):
        self.exps = exps
        self.children = exps

    def __str__(self):
        return f"{self.exps}\nconst 0\ncall Int:sub"


class VarNode(ASTNode):
    """Integer constant"""
    def __init__(self, var: str, type: str):
        self.const = var
        self.type = type

    def __str__(self):
        return f"const {self.const}"

    def initialization(self, visit_state: List):
        return


class StoreNode(ASTNode):
    """ident   -> call_var"""
    def __init__(self, value: ASTNode):
        self.value = value
        self.children = [value]

    def __str__(self):
        return f"store {self.value}"

    def initialization(self, visit_state: List):
        return self.value.initialization(visit_state)

###Maybe Init?
class StoreFieldNode(ASTNode):
    def __init__(self,
                 field: ASTNode,
                 value: ASTNode):
        self.field = field
        self.value = value
        self.children = [field, value]

    def __str__(self):
        return f'''{self.field}\nstore_field {self.value}'''


class LoadNode(ASTNode):
    """ident   -> call_var"""
    def __init__(self, value: ASTNode):
        self.value = value
        self.children = [value]

    def __str__(self):
        return f"load {self.value}"

    def initialization(self, visit_state: dict):
        if str(self.value) not in visit_state["def_init"] and str(self.value) not in visit_state["fields"]:
            raise Exception(f"This variable is not initialized : {self.value} not present")

###Maybe Init?
class LoadFieldNode(ASTNode):
    def __init__(self,
                 field: ASTNode,
                 value: ASTNode):
        self.field = field
        self.value = value
        self.children = [field, value]

    def __str__(self):
        return f'''{self.field}\nload_field {self.value}'''


class VarRefNode(ASTNode):
    def __init__(self, name: str):
        assert isinstance(name, str)
        self.name = name

    def __str__(self):
        return f"{self.name}"

    def initialization(self, visit_state: dict):
        return f"{self.name}"


class ASTBuilder(Transformer):
    """Translate Lark tree to AST"""
    def program(self, e):
        log.debug("->program")
        classes, methods, stmt_block = e
        return ProgramNode(classes, methods, stmt_block)

    def classes(self, e):
        return e

    def clazz(self, e):
        log.debug("->clazz")
        name, formals, super, constructor, methods = e
        if formals is None:
            formals = []
        if methods is None:
            methods = []
        return ClassNode(name, formals, super, constructor, methods)

    def methods(self, e):
        return e

    def method(self, e):
        log.debug("->method")
        name, formals, returns, block = e
        if formals is None:
            formals = []
        if returns is None:
            returns = "Obj"
        return MethodNode(name, formals, returns, block)

    def formals(self, e):
        return e

    def formal(self, e):
        log.debug("->formal")
        var_name, var_type = e
        return FormalNode(var_name, var_type)

    def stmt_block(self, e) -> ASTNode:
        log.debug("->block")
        return e

    def assignment(self, e):
        left, ident, right = e
        return AsmtNode(left, ident, right)

    def new(self, e):
        ident, args = e
        return NewNode(ident,args)

    def method_call(self, e):
        '''r_exp "." ident "(" args* ")" ->method_call'''
        if len(e) == 2:
            right, ident = e
            args = []
        else:
            right, ident, args = e
        return MethodCallNode(ident, right, args)

    def args(self, e):
        value = e[0]
        return ArgsNode(value)

    def while_stmt(self, e) -> ASTNode:
        log.debug("->while_stmt")
        cond, whilepart = e
        return WhileNode(cond, whilepart)

    def if_stmt(self, e) -> ASTNode:
        log.debug("->if_stmt")
        if len(e) == 2:
            cond, thenpart = e
            elsepart = []
        else:
            cond, thenpart, elsepart = e
        return IfNode(cond, thenpart, elsepart)

    def else_stmt(self, e) -> ASTNode:
        log.debug("->elseblock")
        return e[0]  # Unwrap one level of block

    def condition(self, e):
        log.debug("->condition")
        return e

    def nots(self, e):
        log.debug("->not")
        return NotNode(e[0])

    def bool_and(self, e):
        left, right = e
        return AndNode(left, right)

    def bool_or(self, e):
        left, right = e
        return OrNode(left, right)

    def less_than(self, e):
        left, right = e
        return ComparisonNode("less", left, right)

    def greater_than(self, e):
        left, right = e
        return NotNode(AndNode(ComparisonNode("less", left, right), ComparisonNode("equals", left, right)))

    def less_equal(self, e):
        left, right = e
        return AndNode(ComparisonNode("less", left, right), ComparisonNode("equals", left, right))

    def greater_equal(self, e):
        left, right = e
        return NotNode(ComparisonNode("less", left, right))

    def equals(self, e):
        left, right = e
        return ComparisonNode("equals", left, right)

    def plus(self, e):
        left, right = e
        return ArithNode("plus", left, right)

    def sub(self, e):
        left, right = e
        return ArithNode("sub", left, right)

    def mult(self, e):
        left, right = e
        return ArithNode("mult", left, right)

    def div(self, e):
        left, right = e
        return ArithNode("div", left, right)

    def neg(self, e):
        return NegateNode(e[0])

    def store(self, e):
        return StoreNode(e[0])

    def store_field(self, e):
        field, value = e
        return StoreFieldNode(field, value)

    def load(self, e):
        return LoadNode(e[0])

    def load_field(self, e):
        field, value = e
        return LoadFieldNode(field, value)

    def NAME(self, e):
        log.debug("->variable_ref")
        return VarRefNode(e)

    def const(self, e):
        type = 'Int'
        return VarNode(e[0].value, type)

    def lit_str(self, e):
        type = 'String'
        return VarNode(e[0].value, type)

    def lit_not(self, e):
        type = 'Nothing'
        return VarNode(e[0].value, type)

    def lit_true(self, e):
        type = 'Bool'
        return VarNode(e[0].value, type)

    def lit_false(self, e):
        type = 'Bool'
        return VarNode(e[0].value, type)

    def returns(self, e):
        return ReturnNode(e)



def set_default(obj):
    if isinstance(obj, set):
        return list(obj)
    raise TypeError

def main():
    quack_parser = Lark(open("orilib/quack_grammar.txt"), parser='lalr')
    quack = quack_parser.parse
    code = sys.stdin.read()
    tree = quack(code)
    #print(tree.pretty())

    #ultimate transformation
    ast: ASTNode = ASTBuilder().transform(tree)
    #thank you, Pranav
    builtins = open("orilib/builtin_methods.json")
    symtab = json.load(builtins)
    #walk to initialize and type check
    ast.initialization(symtab)
    print(ast)
    json.dumps(symtab,indent=4, default=set_default)

    f = open("./Quack.asm", "w")
    f.write(str(ast))
    f.close()

    #os.system('python assemble.py Quack.asm OBJ/Quack.json')


if __name__ == '__main__':
    if len(sys.argv) < 1:
        print("Need more argument")
        sys.exit(1)
    main()
    #os.system('./bin/tiny_vm Quack')