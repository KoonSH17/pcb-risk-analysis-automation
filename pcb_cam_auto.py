#######################################################################################################################################################
# Author: Si Hui Koon                                                                                                                                 #
# Last updated: 2022                                                                                                                             #
# Summary: This script runs the interface of the GUI and calls the functions that run the automation (from pcb_cam_auto_support.py) whe button press. #
#          For GUI to appear, run pcb_cam_auto.py instead of pcb_cam_auto_support.py.                                                                 #
#######################################################################################################################################################

#Usually dont need to edit this file, just leave it as it is unless you want to change the GUI look
#Functions are in pcb_cam_auto_support.py
import sys
import tkinter as tk
import tkinter.ttk as ttk
from tkinter.constants import *
from tkinter import filedialog as fd
from tkinter.messagebox import showinfo
import os
import pcb_cam_auto_support

class Toplevel1:
    def __init__(self, top=None):
        '''This class configures and populates the toplevel window.
           top is the toplevel containing window.'''
        _bgcolor = '#d9d9d9'  # X11 color: 'gray85'
        _fgcolor = '#000000'  # X11 color: 'black'
        _compcolor = '#d9d9d9' # X11 color: 'gray85'
        _ana1color = '#d9d9d9' # X11 color: 'gray85'
        _ana2color = '#ececec' # Closest X11 color: 'gray92'

        top.geometry("391x123+512+345")
        top.minsize(120, 1)
        top.maxsize(1924, 1061)
        top.resizable(0,  0)
        top.title("PCB CAM AUTO")
        top.configure(background="#ffffff")

        self.top = top

        #button assignment
        self.Button1 = tk.Button(self.top)
        self.Button1.place(relx=0.281, rely=0.244, height=44, width=177)
        self.Button1.configure(activebackground="#ececec")
        self.Button1.configure(activeforeground="#000000")
        self.Button1.configure(background="#d9d9d9")
        self.Button1.configure(command=pcb_cam_auto_support.open_file) ###function in pcb_cam_auto_support.py is assigned to this button
        self.Button1.configure(compound='left')
        self.Button1.configure(disabledforeground="#a3a3a3")
        self.Button1.configure(foreground="#000000")
        self.Button1.configure(highlightbackground="#d9d9d9")
        self.Button1.configure(highlightcolor="black")
        self.Button1.configure(pady="0")
        self.Button1.configure(text='''Load file into PCB CAM''')

def start_up():
    pcb_cam_auto_support.main()

if __name__ == '__main__':
    pcb_cam_auto_support.main()




