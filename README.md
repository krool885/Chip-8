An interpreter for the Chip-8 platform/language implemented in python with minimal dependencies.

The interpreter is ran from the command line and relies on tkinter for the chip-8 display window. Accuracy is pretty good but not perfect especially when it comes to sound, as it seems like all interpreters deal with sound in different ways. The interpreter is released under a GNU license.

usage:
    
    Chip-8.py [-s] [-bc] [-fc] [-m] [-clk] [-f]

where:

        -s turns sound on, default = off        NOTE: sound only works on windows, do not enable if platform is not windows.
        
        -bc [tkinter colour] sets background colour, default = white

        -fc [tkinter colour] sets foreground color, default = black

        -m turns on memory moniter mode for debugging, default = off

        -clk <1/2/3> sets processor clock speed, with 3 being the slowest, 1 being fastest. Default = 2

        -f <file> sets the file you want to run, the default is the included demo program by David Winter. 

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
