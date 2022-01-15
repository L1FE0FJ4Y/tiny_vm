.class Sample:Obj

.method $constructor
const 10
const 5
call Int:plus
const 0
const 1
call Int:sub
call Int:mult
const 4
call Int:mult
const "-(10+5)*4 = "
call String:print
pop
call Int:print
pop
const "\n"
call  String:print
pop
const "Operation Done"
call String:print
pop
return 0