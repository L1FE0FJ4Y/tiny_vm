# Quack
A compiler for an object-oriented programming language Quack.

## Work in progress

This is intended to become the core of an interpreter for the Winter 2022
offering of CIS 461/561 compiler construction course at University of Oregon, 
if I can ready it in time. 

## How to use asm_generator

Type code in text file and run following command with corresponding text file name

```
python3 compile.py < any.txt
```
Running samples :
```
python3 compile.py < ./samples/any.txt
```
After succesful execution, it will return a asembly file called "Quack.asm"

## Progress

#Finished Tasks
- Grammar is finished
- AST tree generation is completed
- Initialization is completed

#Samples
-Used test samples are in samples directory

#Need to be fixed
- Type Checking is still not yet modified
- Work after type checking is not implemented yet

#Future Work
- Once the Type Checking is done, the compiler can compile any Quack languages
