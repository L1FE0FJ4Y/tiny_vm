# tiny_vm
A tiny virtual machine interpreter for Quack programs

## Work in progress

This is intended to become the core of an interpreter for the Winter 2022
offering of CIS 461/561 compiler construction course at University of Oregon, 
if I can ready it in time. 

## How to use asm_generator

Simply run "python exp_translator" (abbreviation of "expression translator" <br />
Then type any integer operation that you would like to calculate.<br />
ex)     > (-5-5)/10 <br />
Then the program automatically generate .asm file and translate into .json file. <br />
Lastly, run the tiny_vm, then it will present result of expression that you entered.
