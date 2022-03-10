
.class $Main:Obj
.method not_duck_typing
.args x
.local a,b
const 7
load x
call Obj:less
jump_if else_12
jump then_11
then_11:
const 42
store a
const 13
store b
jump endif_13
else_12:
const "forty-two"
store a
const "thirteen"
store b
endif_13:
load b
load a
call Obj:less
jump_if then_14
jump else_15
then_14:
const 1
jump endif_16
else_15:
const 2
endif_16:
return 1

.method $constructor
.local halo
const 1
store halo
cond_17:
const 0
load halo
call Obj:less
jump_if and_20
jump loop_18
and_20:
const 0
load halo
call Obj:equals
jump_if endloop_19
jump loop_18
loop_18:
load halo
call Obj:print
const 1
load halo
call :sub
store halo
jump cond_17
endloop_19:
const nothing
return 0