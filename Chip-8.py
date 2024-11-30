#A chip-8 emulator written in python - just for fun!
import random
import time
import msvcrt as k
import winsound as s
import math
import tkinter as tk
import threading
import sys
import queue

#creating the queue cause we need threading.
message_queue = queue.Queue(maxsize=5)

#Chip-8's built in font, loaded into 0000h to 01FFh during setup
fntZero = ["11110000","10010000","10010000","10010000","11110000"]
fntOne = ["00100000","01100000","00100000","00100000","01110000"]
fntTwo = ["11110000","00010000","11110000","10000000","11110000"]
fntThree = ["11110000","00010000","11110000","00010000","11110000"]
fntFour = ["10010000","10010000","11110000","00010000","00010000"]
fntFive = ["11110000","10000000","11110000","00010000","11110000"]
fntSix = ["11110000","10000000","11110000","10010000","11110000"]
fntSeven = ["11110000","00010000","00100000","01000000","01000000"]
fntEight = ["11110000","10010000","11110000","10010000","11110000"]
fntNine = ["11110000","10010000","11110000","00010000","11110000"]
fntA = ["11110000","10010000","11110000","10010000","10010000"]
fntB = ["11100000","10010000","11100000","10010000","11100000"]
fntC = ["11110000","10000000","10000000","10000000","11110000"]
fntD = ["11100000","10010000","10010000","10010000","11100000"]
fntE = ["11110000","10000000","11110000","10000000","11110000"]
fntF = ["11110000","10000000","11110000","10000000","10000000"]
font = [fntZero,fntOne,fntTwo,fntThree,fntFour,fntFive,fntSix,fntSeven,fntEight,
        fntNine,fntA,fntB,fntC,fntD,fntE,fntF]

#Keyboard mappings: 
keydict = {
    "0": "c",
    "1": "2",
    "2": "3",
    "3": "4",
    "4": "w",
    "5": "e",
    "6": "r",
    "7": "s",
    "8": "d",
    "9": "f",
    "a": "x",
    "b": "v",
    "c": "5",
    "d": "t",
    "e": "g",
    "f": "b"
    }

rkeydict = {
    "c": "0",
    "2": "1",
    "3": "2",
    "4": "3",
    "w": "4",
    "e": "5",
    "r": "6",
    "s": "7",
    "d": "8",
    "f": "9",
    "x": "a",
    "v": "b",
    "5": "c",
    "t": "d",
    "g": "e",
    "b": "f",
    }


def setup():
    with open("pong.ch8","rb") as file:
        raw = file.read()
        data = []
        for i in range(0,len(raw)):
            data.append(int(raw[i]))
    #We now have our file as bytes

    
    memory = [0]*4096   #Memory map is simply a big list of integers.
    for i in range(0,512): #000h to 1FFh is filled with FF to distinguish it
        memory[i] = int("11111111",2)

    for i in range(0,32):
        memory[i+80] = 0   #first 32 bytes used for the stack. 16, 16 bit values storable.
    
    for i in range(0,16):   #Loop that loads font data into the first 80 bytes.
        for j in range(0,5):
            memory[(i*5)+j] = int(font[i][j],2)

    for i in range(0,256):     #starting at 070h we have screen ram. This isnt a standardised location so no you cannot access it from within a program.
        memory[i+int("70",16)] = 0
        # The display is monochrome and 64x32 pixels. Each bit corresponds to a single pixel
        # The actual graphics are created using "sprites" using the relevant instructions.

    #Now putting program into memory.
    for i in range(0,len(data)):
        memory[i + 512] = data[i]

    return memory

def display(memory,moniter):
    global dispstr
    vram = []   #converts VRAM into a list of binary digits.
    for i in range(int("70",16),int("70",16)+256):
        for j in range(0,8):
            val = bin(memory[i])
            val = str(val[2:])
            val = val.rjust(8,"0")
            vram.append(val[j])


    dispstr = ""
    for i in range(0,32):
        for j in range(0,64):
            if vram[64*i + j] == "1":
                dispstr = dispstr + "█"
            else:
                dispstr = dispstr + " "
    try:
        message_queue.put_nowait("display update")
    except queue.Full:
        pass

    

def interpreter(memory):
    print("interpreter start")
    global key
    register = [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0, 0, 0, 0,]
    timer = [0,0]
    #registers[0] - registers[15] are V0-VF and are 8 bit. VF is reserved for flags.
    #register[16] is I, and is 16 bit
    #register[17] is the stack pointer, as it doesn't matter how many bits it is really. The stack is the first 32 bytes of ram.
    #register[18] is the PC, and is 16 bit.
    #the two timer values are the delay and sound timers. They are both 8 bit.
    
    register[18] = 512  #Initialises PC to standard entrypoint of 200h
    register[17] = 80   #Initialises SP to 80 which is where the stack starts.

    cpucycle = 0
    stime = math.floor((time.time() % 1)*60)
    moniter = True
    snd = 0         # an internal state variable for sound duration.

    while True:
        high = hex(memory[register[18]])[2:]
        low = hex(memory[register[18]+1])[2:]
        high = high.zfill(2)
        low = low.zfill(2)
        ir = high + low
        if moniter:
            print(ir)
            print(register)


        if ir[0] == "0":        #The code block for handling 0 series instructions.
            if ir[1] == "0" and ir[2] == "e" and ir[3] == "e":
                #This is the RET instruction.
                #dcrements stack pointer.
                register[17] -= 2
                jmphg = hex(memory[register[17]])[2:]        #retrieves high and low byte of new address
                jmplw = hex(memory[register[17]+1])[2:]
                jmplw = jmplw.zfill(2)
                jmphg = jmphg.zfill(2)
                jmp = int(jmphg + jmplw,16)
                
                register[18] = jmp           #sets PC to new address
                
            elif ir[1] == "0" and ir[2] == "e" and ir[3] == "0":
                #This is the CLS instruction.
                for i in range(int("70",16),int("70",16)+30):
                    memory[i] = 0

            else:
                #This is the SYS instruction, ignored by modern interpreters.
                pass

        elif ir[0] == "1":      #The code for handling 1 series instructions.
            #Theres only one, the JMP instruction.
            jmp = ir[1:] #extracts last 3 digits.
            register[18] = int(jmp,16)-2    #subtract 2 to account for the incrementing of the PC at the end of this loop

        elif ir[0] == "2":
            #This is the CALL instruction.
            currentPC = register[18]
            if currentPC < 255:
                PChg = 0
                PClw = currentPC
            else:
                currentPC = hex(currentPC)[2:]
                PChg = int(currentPC[0],16)
                PClw = int(currentPC[1:3],16)


            memory[register[17]] = PChg
            register[17] += 1
            memory[register[17]] = PClw #The old PC should now be on the stack.
            register[17] += 1            

            newPC = ir[1:]
            register[18] = int(newPC,16) - 2

        elif ir[0] == "3":
            #This is the SE instruction (skip next instruction on equal).
            reg = int(ir[1],16)
            op1 = int(ir[2:4],16)
            if register[reg] == op1:
                register[18] += 2

        elif ir[0] == "4":
            #This is the SNE instruction (skip next instruction on not equal).
            reg = int(ir[1],16)
            op1 = int(ir[2:4],16)
            if register[reg] != op1:
                register[18] += 2

        elif ir[0] == "5":
            #This is the SE instruction, except for 2 registers.
            reg1 = int(ir[1],16)
            reg2 = int(ir[2],16)
            if register[reg1] == register[reg2]:
                register[18] += 2

        elif ir[0] == "6":
            #This is the LD command
            reg = int(ir[1],16)
            op1 = int(ir[2:4],16)
            register[reg] = op1

        elif ir[0] == "7":
            #This is the ADD command
            reg = int(ir[1],16)
            op1 = int(ir[2:4],16)
            num = register[reg] + op1
            if num > 255:
                num -= 256
            register[reg] = num

        if ir[0] == "8":        #The 8 series instructions are the main arithmetic ones.
            if ir[3] == "0":
                #This is the LD instruction for registers
                reg1 = int(ir[1],16)
                reg2 = int(ir[2],16)
                register[reg1] = register[reg2]

            elif ir[3] == "1":
                #This is the OR instruction.
                reg1 = int(ir[1],16)
                reg2 = int(ir[2],16)

                num = register[reg1] | register[reg2]
                register[reg1] = num

            elif ir[3] == "2":
                #This is the AND instruction
                reg1 = int(ir[1],16)
                reg2 = int(ir[2],16)

                num = register[reg1] & register[reg2]
                register[reg1] = num

            elif ir[3] == "3":
                #This is the XOR instruction
                reg1 = int(ir[1],16)
                reg2 = int(ir[2],16)

                num = register[reg1] ^ register[reg2]
                register[reg1] = num

            elif ir[3] == "4":
                #This is ADD for registers
                reg1 = int(ir[1],16)
                reg2 = int(ir[2],16)

                num = register[reg1] + register[reg2]
                if num > 255:
                    register[15] = 1    #sets the overflow in the flag register.
                    num -= 256
                else:
                    register[15] = 0
                register[reg1] = num

            elif ir[3] == "5":
                #This is the SUB instruction
                reg1 = int(ir[1],16)
                reg2 = int(ir[2],16)

                num = register[reg1] - register[reg2]
                
                if register[reg1] > register[reg2]:
                    register[15] = 1    #sets "not borrow" in the flag register.
                else:
                    register[15] = 0
                    num = abs(num)

                register[reg1] = num

            elif ir[3] == "6":
                #This is the SHR instruction
                reg1 = int(ir[1],16)
                num = register[reg1]
                if bin(num)[7] == "1":
                    register[15] = 1    #Sets the overflow in the flag register.
                else:
                    register[15] = 0

                register[reg1] = int(num/2)

            elif ir[3] == "7":
                #This is the SUBN instruction
                reg1 = int(ir[1],16)
                reg2 = int(ir[2],16)

                num = register[reg2] - register[reg1]
                
                if register[reg2] > register[reg1]:
                    register[15] = 1    #sets "not borrow" in the flag register.
                else:
                    register[15] = 0
                    num = abs(num)

                register[reg1] = num

            elif ir[3] == "e":
                #This is the SHL instruction
                reg1 = int(ir[1],16)
                num = register[reg1]
                num2 = int(num*2)
                if bin(num)[0] == "1":
                    register[15] = 1    #Sets the overflow in the flag register.
                    num2 -= 256
                else:
                    register[15] = 0

                register[reg1] = num2

        elif ir[0] == "9":
            #This is the SNE instruction for registers (skip next instruction on not equal).
            reg1 = int(ir[1],16)
            reg2 = int(ir[2],16)
            if register[reg1] != register[reg2]:
                register[18] += 2

        elif ir[0] == "a":
            #This is the LD instruction for the I register
            num = int(ir[1:4],16)
            register[16] = num

        elif ir[0] == "b":
            #This is the JP instruction with offset
            num = int(ir[1:4],16)
            num += register[0]

            register[18] == num

        elif ir[0] == "c":
            #This is the RND instruction.
            reg1 = int(ir[1],16)
            op1 = int(ir[2:4],16)
            num = random.randint(0,255)
            num = num & op1
            #num = 1
            register[reg1] = num

        elif ir[0] == "d":
            #This is the DRW instruction.
            register[15] = 0    #clears VF as a default
            x = register[int(ir[1],16)]
            y = register[int(ir[2],16)]
            num = int(ir[3],16)
            address = register[16]

            sprite = []     #extracts sprite data from memeory
            for i in range(address,address+num):
                for j in range(0,8):
                    val = bin(memory[i])
                    val = val[2:]
                    val = val.zfill(8)
                    sprite.append(val[j])
                    

            vram = []   #converts VRAM into a list of binary digits.
            for i in range(int("70",16),int("70",16)+256):
                for j in range(0,8):
                    val = bin(memory[i])
                    val = val[2:]
                    val = val.zfill(8)
                    vram.append(val[j])
                    
            
            tempx = x
            tempy = y
            for i in range(0,len(sprite)):
                tempx = x + i%8
                tempy = y + i // 8

                tempx = tempx % 64  #For wrap around
                tempy = tempy % 32
                
                address = tempy*64 + tempx

                val = "0"
                if vram[address] == "1" and sprite[i] == "1":
                    val = "0"
                    register[15] = 1
                elif vram[address] == "1" or sprite[i] == "1":
                    val = "1"
                vram[address] = val

            nvram = []
            for i in range(0,256):
                byte = []
                for j in range(0,8):
                    byte.append(vram[(i*8)+j])
                byte = "".join(byte)
                nvram.append(byte)

            for i in range(0,256):
                memory[i+int("70",16)] = int(nvram[i],2)

            display(memory,moniter)

        elif ir[0] == "e":
            if ir[2:4] == "a1":
                #This is SKNP,skip next instruction on key not pressed.
                tkey = str(register[int(ir[1])])
                if key in rkeydict:
                    if rkeydict[key] == tkey:
                        pass
                    else:
                        register[18] += 2
                else:
                    register[18] += 2
                #key = ""


            if ir[2:4] == "9e":         #not used in pong
                #This is SKP,skip next instruction on key pressed.
                tkey = register[int(ir[1])]
                if key in rkeydict:
                    if rkeydict[key] == str(tkey):
                        register[18] += 2
                        #key = ""
    
        elif ir[0] == "f":
            if ir[2:4] == "07":
                #This is the load delay timer instruction
                reg = int(ir[1],16)
                register[reg] = timer[0]

            elif ir[2:4] == "0a":
                #This is the load key instruction. Pauses all execution while waiting for a keypress.
                reg = int(ir[1],16)
                while key == "" or key not in rkeydict:
                    pass
                nkey = key
                nkey = rkeydict[nkey]
                key = ""
                register[reg] = int(nkey,16)

            elif ir[2:4] == "15":
                #This is the set delay timer instruction.
                reg = int(ir[1],16)
                timer[0] = register[reg]

            elif ir[2:4] == "18":
                #This is set sound timer.
                reg = int(ir[1],16)
                timer[1] = register[reg]

            elif ir[2:4] == "1E":
                #This is the ADD I instruction.
                reg = int(ir[1],16)
                register[16] = register[16] + register[reg]
                if register[16] > 65535:
                    register[16] -= 65536

            elif ir[2:4] == "29":
                #This is the "set I to location of digit in Vx" instruction.
                reg = int(ir[1],16)
                num = register[reg]
                if num >= 16:
                    pass
                else:
                    register[16] = (num*5)

            elif ir[2:4] == "33":
                #This is the store BCD instruction.
                reg = int(ir[1],16)
                num = str(register[reg])
                if len(num) > 2:
                    Dig1 = int(num[0])
                    Dig2 = int(num[1])
                    Dig3 = int(num[2])
                elif len(num) > 1:
                    Dig1 = 0
                    Dig2 = int(num[0])
                    Dig3 = int(num[1])
                else:
                    Dig1 = 0
                    Dig2 = 0
                    Dig3 = int(num[0])
                memory[register[16]] = Dig1
                memory[register[16]+1] = Dig2
                memory[register[16]+2] = Dig3

            elif ir[2:4] == "55":
                #This is store registers v0 - vx at I
                reg = int(ir[1],16)
                for i in range(0,reg+1):
                    memory[register[16]+i] = register[i]

            elif ir[2:4] == "65":
                reg = int(ir[1],16)
                for i in range(0,reg+1):
                    register[i] = memory[register[16]+i]

        ctime = math.floor((time.time() % 1)*60)
        if ctime != stime:
            stime = ctime
            timer[0] -= 1
            if timer[0] < 0:
                timer[0] = 0
            timer[1] -= 1
            if timer[1] < 0:
                timer[1] = 0
            
            if timer[1] != 0:
                s.Beep(900,60)
                

        if not moniter:
            cpucycle += 1
            if cpucycle == 5:        #Batches instructions in 20s, then waits 0.04 seconds for an effective speed of 500Hz.
                time.sleep(0.01)
                cpucycle = 0
                display(memory,moniter)
            if key == "m":
                moniter = True
                key = ""
        else:
            inp = input("> ")
            if inp == "s":
                cpucycle += 1
            if inp == "endm":
                moniter = False
            if inp == "k":
                if key in rkeydict:
                    chkey = rkeydict[key]
                else:
                    chkey = "n/a"
                print(F"raw: {key}, translated: {chkey}")
            if inp == "ma":
                print(memory)
            if inp[0] == "m":
                try:
                    print(memory[int(inp[1:])])
                except ValueError:
                    print("address doesn't exist")
            if inp == "r":
                print(register)
            if inp == "pc":
                print(register[18])

        register[18] += 2   #increments program counter.


def on_close(window):
    window.destroy()
    sys.exit()

def keyhndl(event):
    global key
    key = event.char

def safedisplay(disp,dispstr):      #threading stuff, tkinter isn't thread safe.
    disp.after(0, lambda: updatedisplay(dispstr))

def updatedisplay(dispstr):     #code that actually puts the text into the widget.
    disp.config(state="normal")
    disp.delete("1.0","end")
    disp.insert(tk.END, dispstr)
    disp.config(state="disabled")
    disp.see(tk.END)
    
def processqueue():
    if not message_queue.empty():
        msg = message_queue.get_nowait()
        updatedisplay(dispstr)

    disp.after(16, processqueue)    #should check queue roughly when a new event is added.
    
def main():
    global key
    global disp
    global dispstr
    key = ""
    dispstr = "a"
    
    window = tk.Tk()
    label = tk.Label(window, text="Chip-8")
    label.pack()

    disp = tk.Text(window,state="disabled",height = 32, width = 64)
    disp.bind("<Key>", keyhndl)
    disp.pack()

    processqueue()
    
    memory = setup()
    thread = threading.Thread(target=interpreter, args=(memory,), daemon=True)
    thread.start()

    window.protocol("WM_DELETE_WINDOW", lambda: on_close(window)) #binds the on_close() function to the tkinter window being closed.

    tk.mainloop()

    
main()
