# Kind-Duplicate-Finder
This program will find duplicate files in a directory.
I developed this program in Python in my free time.
Tried to keep the code as clean as possible with a lot of documentations.
The program uses Tkinter for the GUI. I also followed MVC pattern as I understood it and as I found the most right to implement 
in order for the code to be understandable.

To find duplicates the program first groups file of same size, if more than one file of same size is in a group then from this moment hash 
value is calculated for every file in this size group and those file now grouped by size and and inside the size group, by their hash value.
This saves up calculating the hash for every file. Instead the hash value of a file is calculated if there is a file with the same size.
I know there may be hash collisions with file of different sizes. Hence there is the option of "slow" hash function that reduces the
chances for hash collision.
