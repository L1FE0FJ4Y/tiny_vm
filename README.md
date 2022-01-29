# tiny_vm
A tiny virtual machine interpreter for Quack programs

## Work in progress

This is intended to become the core of an interpreter for the Winter 2022
offering of CIS 461/561 compiler construction course at University of Oregon, 
if I can ready it in time. 

## How to use asm_generator

Insert any calls that you want to try in the "quack.txt" <br />
Simply run "python quack_quack.py < quack.txt" <br />

Then the program automatically generate Quack.asm file and translate into Quack.json file. <br />
Lastly, it runs Ori_VM with the Quack.json file, and present result of the quack.txt.
