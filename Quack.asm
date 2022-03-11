
.class $Main:Obj
.method bad_init
.local n_reps,rep
const 0
store rep
const 3
store n_reps
cond_4:
load n_reps
load rep
call Obj:less
jump_if loop_5
jump endloop_6
loop_5:

jump cond_4
endloop_6:
const nothing
return 0

.method $constructor

const nothing
return 0