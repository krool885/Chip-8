#A chip-8 emulator written in python - just for fun!
import random
import time
import msvcrt as k
import math
import tkinter as tk
import threading
import sys
import queue
import platform

if platform.system() == "Windows":
    import winsound as s

#creating the queue cause we need threading.
dqueue = queue.Queue(maxsize=5)
kqueue = queue.Queue(maxsize=3)

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

class Vmachine:
    def __init__(self):
        self.cmdargs() #parses the arguments passed via command line
        
        try:
            with open(self.file,"rb") as file:
                raw = file.read()
                data = []
                for i in range(0,len(raw)):
                        data.append(int(raw[i]))
                #We now have our file as bytes
        except FileNotFoundError:
            print("file not found")
            sys.exit()

        
        tmemory = [0]*4096   #Memory map is simply a big list of integers.
        for i in range(0,512): #000h to 1FFh is filled with FF to distinguish it
            tmemory[i] = int("11111111",2)

        for i in range(0,32):
            tmemory[i+80] = 0   #first 32 bytes after font used for the stack. 16, 16 bit values storable.
        
        for i in range(0,16):   #Loop that loads font data into the first 80 bytes.
            for j in range(0,5):
                tmemory[(i*5)+j] = int(font[i][j],2)

        for i in range(0,256):     #starting at 070h we have screen ram. This isnt a standardised location so no you cannot access it from within a program.
            tmemory[i+int("70",16)] = 0
            # The display is monochrome and 64x32 pixels. Each bit corresponds to a single pixel
            # The actual graphics are created using "sprites" using the relevant instructions.

        #Now putting program into memory.
        for i in range(0,len(data)):
            tmemory[i + 512] = data[i]

        self.memory = tmemory


        #Keyboard mappings: 
        self.keydict = {
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

        self.rkeydict = {
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

        self.cpucycle = 0
        self.stime = math.floor((time.time() % 1)*60)
        self.snd = 0         # an internal state variable for sound duration.
        self.key = ""

    def cmdargs(self):
        rawarguments = sys.argv[1:]
        arguments = []
        i = 0
        while i < len(rawarguments):
            block = []
            if rawarguments[i][0] == "-":
                block.append(rawarguments[i].lower())
                if i != len(rawarguments)-1:
                    if rawarguments[i+1][0] != "-":
                        block.append(rawarguments[i+1].lower())
                        i += 1
            else:
                block = rawarguments[i]
            i += 1
            arguments.append(block)

        self.sound = False
        self.bc = "White"
        self.fc = "Black"
        self.moniter = False
        self.clk = 0.010
        self.file = "demo.ch8"
        
        for block in arguments:
            if block[0] == "-s":
                self.sound = True

            elif block[0] == "-bc":
                self.bc = block[1]

            elif block[0] == "-fc":
                self.fc = block[1]

            elif block[0] == "-m":
                self.moniter = True

            elif block[0] == "-clk":
                if block[1] == "1":
                    self.clk = 0.005
                elif block[1] == "2":
                    self.clk = 0.010
                elif block[1] == "3":
                    self.clk = 0.020
                else:
                    print("invalid clock setting")

            elif block[0] == "-f":
                self.file = block[1]

            else:
                print("""
This is a simple Chip-8 interpreter/VM.

usage:
    Chip-8.py [-s] [-bc] [-fc] [-m] [-clk] [-f]

    where:

        -s turns sound on, default = off        NOTE: sound only works on windows, do not enable if platform is not windows.
        
        -bc [tkinter colour] sets background colour, default = white

        -fc [tkinter colour] sets foreground color, default = black

        -m turns on memory moniter mode for debugging, default = off

        -clk <1/2/3> sets processor clock speed, with 3 being the slowest, 1 being fastest. Default = 2

        -f <file> sets the file you want to run, the default is the included demo.

    Input is done via a hexidecimal keypad structured like so:

        | 1 | 2 | 3 | C |
        | 4 | 5 | 6 | D |
        | 7 | 8 | 9 | E |
        | A | 0 | B | F |

    which is mapped onto the 4x4 grid of keys:

        | 2 | 3 | 4 | 5 |
        | W | E | R | T |
        | S | D | F | G |
        | X | C | V | B |

    Additionally, pressing m during execution will enter moniter mode.


Written by Lily Allenby.
""")
                sys.exit()

    def display(self):
        vram = []   #converts VRAM into a list of binary digits.
        for i in range(int("70",16),int("70",16)+256):
            for j in range(0,8):
                val = bin(self.memory[i])
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
            dqueue.put_nowait("d" + dispstr)
        except queue.Full:
            pass
    
    def interpreter(self):
        print("interpreter start")
        register = [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0, 0, 0, 0,]
        timer = [0,0]
        #registers[0] - registers[15] are V0-VF and are 8 bit. VF is reserved for flags.
        #register[16] is I, and is 16 bit
        #register[17] is the stack pointer, as it doesn't matter how many bits it is really. The stack is the first 32 bytes of ram.
        #register[18] is the PC, and is 16 bit.
        #the two timer values are the delay and sound timers. They are both 8 bit.
        
        register[18] = 512  #Initialises PC to standard entrypoint of 200h
        register[17] = 80   #Initialises SP to 80 which is where the stack starts.


        while True:
            high = hex(self.memory[register[18]])[2:]
            low = hex(self.memory[register[18]+1])[2:]
            high = high.zfill(2)
            low = low.zfill(2)
            ir = high + low
            if self.moniter:
                print(ir)
                print(register)
                print(timer)
            
            if not kqueue.empty():       #The keyrecieve to the window objects keysend
                msg = kqueue.get_nowait()
                self.key = msg[1]
                kqueue.task_done()
                

            if ir[0] == "0":        #The code block for handling 0 series instructions.
                if ir[1] == "0" and ir[2] == "e" and ir[3] == "e":
                    #This is the RET instruction.
                    #dcrements stack pointer.
                    register[17] -= 2
                    jmphg = hex(self.memory[register[17]])[2:]        #retrieves high and low byte of new address
                    jmplw = hex(self.memory[register[17]+1])[2:]
                    jmplw = jmplw.zfill(2)
                    jmphg = jmphg.zfill(2)
                    jmp = int(jmphg + jmplw,16)
                    
                    register[18] = jmp           #sets PC to new address
                    
                elif ir[1] == "0" and ir[2] == "e" and ir[3] == "0":
                    #This is the CLS instruction.
                    for i in range(int("70",16),int("70",16)+256):
                        self.memory[i] = 0

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


                self.memory[register[17]] = PChg
                register[17] += 1
                self.memory[register[17]] = PClw #The old PC should now be on the stack.
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
                    if (bin(num)[2:].zfill(8))[7] == "1":
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
                        val = bin(self.memory[i])
                        val = val[2:]
                        val = val.zfill(8)
                        sprite.append(val[j])
                        

                vram = []   #converts VRAM into a list of binary digits.
                for i in range(int("70",16),int("70",16)+256):
                    for j in range(0,8):
                        val = bin(self.memory[i])
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
                    self.memory[i+int("70",16)] = int(nvram[i],2)

                self.display()

            elif ir[0] == "e":
                if ir[2:4] == "a1":
                    #This is SKNP,skip next instruction on key not pressed.
                    tkey = str(register[int(ir[1])])
                    if self.key in self.rkeydict:
                        if self.rkeydict[self.key] == tkey:
                            pass
                        else:
                            register[18] += 2
                    else:
                        register[18] += 2
                    #self.key = ""


                if ir[2:4] == "9e":         #not used in pong
                    #This is SKP,skip next instruction on key pressed.
                    tkey = register[int(ir[1])]
                    if self.key in self.rkeydict:
                        if self.rkeydict[self.key] == str(tkey):
                            register[18] += 2
                            #self.key = ""
        
            elif ir[0] == "f":
                if ir[2:4] == "07":
                    #This is the load delay timer instruction
                    reg = int(ir[1],16)
                    register[reg] = timer[0]

                elif ir[2:4] == "0a":
                    #This is the load key instruction. Pauses all execution while waiting for a keypress.
                    reg = int(ir[1],16)
                    while self.key == "" or self.key not in self.rkeydict:
                        pass
                    nkey = self.key
                    nkey = self.rkeydict[nkey]
                    self.key = ""
                    register[reg] = int(nkey,16)

                elif ir[2:4] == "15":
                    #This is the set delay timer instruction.
                    reg = int(ir[1],16)
                    timer[0] = register[reg]

                elif ir[2:4] == "18":
                    #This is set sound timer.
                    reg = int(ir[1],16)
                    timer[1] = register[reg]

                elif ir[2:4] == "1e":
                    #This is the ADD I instruction.
                    reg = int(ir[1],16)
                    register[16] += register[reg]
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
                    self.memory[register[16]] = Dig1
                    self.memory[register[16]+1] = Dig2
                    self.memory[register[16]+2] = Dig3

                elif ir[2:4] == "55":
                    #This is store registers v0 - vx at I
                    reg = int(ir[1],16)
                    for i in range(0,reg+1):
                        self.memory[register[16]+i] = register[i]

                elif ir[2:4] == "65":
                    reg = int(ir[1],16)
                    for i in range(0,reg+1):
                        register[i] = self.memory[register[16]+i]

            ctime = math.floor((time.time() % 1)*60)
            if ctime != self.stime:
                self.stime = ctime
                timer[0] -= 1
                if timer[0] < 0:
                    timer[0] = 0
                timer[1] -= 1
                if timer[1] < 0:
                    timer[1] = 0
                
                if timer[1] != 0:
                    if self.sound == True:  
                        s.Beep(700,40)
                    

            if not self.moniter:
                self.cpucycle += 1
                if self.cpucycle == 5:        #Batches instructions in 20s, then waits 0.04 seconds for an effective speed of 500Hz.
                    time.sleep(self.clk)
                    self.cpucycle = 0
                    self.display()
                if self.key == "m":
                    self.moniter = True
                    self.key = ""
            else:
                inp = input("> ")
                if inp == "s":
                    self.cpucycle += 1
                if inp == "endm":
                    self.moniter = False
                if inp == "k":
                    if self.key in self.rkeydict:
                        chkey = self.rkeydict[self.key]
                    else:
                        chkey = "n/a"
                    print(F"raw: {self.key}, translated: {chkey}")
                if inp == "ma":
                    print(self.memory)
                if inp[0] == "m":
                    try:
                        print(self.memory[int(inp[1:])])
                    except ValueError:
                        print("address doesn't exist")
                if inp == "r":
                    print(register)
                if inp == "pc":
                    print(register[18])

            register[18] += 2   #increments program counter.

class Window:
    def getcolours(self,bc,fc,file):
        self.bc = bc
        self.fc = fc
        self.file = file

    def onclose(self):
        self.tkwindow.destroy()
        sys.exit()

    def keysend(self,event):
        key = event.char
        if key != " ":
            msg = "k"+key
            try:
                kqueue.put_nowait(msg)
            except queue.Full:
                print("queue full")
                pass

    def updatedisplay(self):     #code that actually puts the text into the widget.
        self.disp.config(state="normal")
        self.disp.delete("1.0","end")
        self.disp.insert(tk.END, self.dispstr)
        self.disp.config(state="disabled")
        self.disp.see(tk.END)
        
    def processqueue(self):
        if not dqueue.empty():
            msg = dqueue.get_nowait()
            self.dispstr = msg[1:]
            self.updatedisplay()
            dqueue.task_done()
        
        self.disp.after(20, self.processqueue)    #checks queue on a regular interval

    def start(self):
        self.dispstr = "a"
        
        self.tkwindow = tk.Tk()
        self.tkwindow.title("Chip-8")
            
        self.label = tk.Label(self.tkwindow, text=self.file)
        self.label.pack()

        try:
            self.disp = tk.Text(self.tkwindow,bg = self.bc, fg = self.fc, state="disabled",height = 32, width = 64)
        except tk.TclError:
            print("Invalid tkinter colour, valid examples include: White, Blue, Red, Green")
            sys.exit()
            
        self.disp.bind("<Key>", self.keysend)
        self.disp.pack()

        self.processqueue()

        self.tkwindow.protocol("WM_DELETE_WINDOW",self.onclose) #binds the on_close() function to the tkinter window being closed.
        
        tk.mainloop()
    
def main():
    vm = Vmachine()
    window = Window()   #creating both window and interpreter objects
    window.getcolours(vm.bc,vm.fc,vm.file)
    
    thread = threading.Thread(target=vm.interpreter, args=(), daemon=True)
    thread.start()  #starting the thread for the interpreter

    window.start()

    
main()
