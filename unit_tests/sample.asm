.class Sample:Obj

.method $constructor
const 0
const 5
call Int:sub
const 5
call Int:sub
const 10
call Int:div
const 0
const 2
call Int:sub
call Int:mult
const 20
call Int:plus
const "(((-5-5)/10)*-2)+20 = "
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