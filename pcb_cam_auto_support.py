#######################################################################################################################################################
# Author: Si Hui Koon                                                                                                                                 #
# Last updated: 2022                                                                                                                             #
# Summary: This script stores the 2 function that run during button press:                                                                            #
#           1. pcb_run(path) takes the path of ODB file chosen by user, opens PCB CAM and runs the automation                                         #
#           2. open_file() is called when GUI button is pressed. Opens up file explorer for user to select ODB file and stores the filepath in 'path' #
#              string. If path is not empty, pcb_run(path) will be called.                                                                            #
#######################################################################################################################################################

import tkinter as tk
from tkinter import filedialog as fd
from tkinter.messagebox import showinfo
from tkinter.messagebox import askyesno
import sys 
import os
import pcb_cam_auto
import pywinauto
from pywinauto.application import Application
from time import sleep
from pywinauto.findwindows import find_windows
import pywinauto.keyboard
from pywinauto import Desktop
import pywinauto.mouse
import os.path
import shutil
import pandas as pd
from PIL import ImageGrab
from PIL import Image
import ctypes
import ctypes.wintypes
from pywinauto.mouse import double_click

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
    
def main(*args):
    '''Main entry point for the application.'''
    global root
    root = tk.Tk()
    root.protocol( 'WM_DELETE_WINDOW' , root.destroy)
    # Creates a toplevel widget.
    global _top1, _w1
    _top1 = root
    _w1 = pcb_cam_auto.Toplevel1(_top1)
    root.mainloop()

#function that does the automation
def pcb_run(path):
    file_name = os.path.basename(path)
    print(f"File name: {file_name}")
    location = os.path.dirname(path)
    print(f"Location: {location}")
    
    # Define monitor constants
    PROCESS_PER_MONITOR_DPI_AWARE = 2
    MDT_EFFECTIVE_DPI = 0
    MONITOR_DEFAULTTOPRIMARY = 1
    
    # Functions to set and get DPI awareness
    SetProcessDpiAwareness = ctypes.windll.shcore.SetProcessDpiAwareness
    GetDpiForMonitor = ctypes.windll.shcore.GetDpiForMonitor
    MonitorFromWindow = ctypes.windll.user32.MonitorFromWindow
    
    # Set the process to be per-monitor DPI aware
    SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE)
    
    # Start PCB CAM Tool
    print("Starting PCB CAM Tool.")
    app = Application(backend='uia').start(cmd_line=r'"C:\CAx\App\PCBCAMTool\PCB-CAM-Tool.exe"')
    sleep(10)  # Wait for app to load
    
    app = Application(backend='uia').connect(path=r"C:\CAx\App\PCBCAMTool\PCB-CAM-Tool.exe")
    window = app['PCB CAM']
    window.set_focus()
    
    # Interact with File menu
    print("Loading ODB to CAMTool.")
    window.File.click_input()
    window.type_keys('{DOWN 2}{ENTER}')
    
    # Load file into PCB CAM
    sleep(2)
    open_file_handle = pywinauto.findwindows.find_windows(title_re="Open")
    app1 = Application().connect(handle=open_file_handle[0])
    open_file_win = app1.window(handle=open_file_handle[0])
    
    # Enter file path in file explorer popup
    open_file_win.child_window(class_name="ToolbarWindow32", found_index=2).click_input(button='right')
    open_file_win.type_keys('{DOWN 3}{ENTER}')
    open_file_win.type_keys(location, with_spaces=True)
    open_file_win.type_keys('{ENTER}')
    open_file_win.Edit.type_keys(file_name, with_spaces=True)
    open_file_win.Open.click_input()
    
    # Close popup message if detected
    sleep(10)
    try:
        question_handle = find_windows(title_re="Question")
        popup = Application().connect(handle=question_handle[0])
        question_win = popup.window(handle=question_handle[0])
        question_win.Yes.click_input()
    except IndexError:
        print("No 'Question' popup detected.")
    
    # Detect and connect to PCB CAM loaded file where the window title changed
    sleep(3)
    windows = Desktop(backend="uia").windows()
    pcb_window = [w.window_text() for w in windows if 'PCB_CAM' in w.window_text()][0]
    app = Application(backend='uia').connect(title=pcb_window, timeout=10)
    print("ODB opened.")
    
    window = app[pcb_window]
    window.maximize()
    sleep(1)
    window.menu_select('Tools->Netlist')
    sleep(1)
    
    # Open CAD Net
    cadnet_handle = find_windows(title_re="CAD Net")[0]
    app2 = Application().connect(handle=cadnet_handle)
    cadnet_win = app2.window(handle=cadnet_handle)
    cadnet_win.maximize()
    print("Netlist tool opened.")
    
    # Find the header control
    header = cadnet_win.child_window(class_name="SysHeader32")
    
    # Get the monitor handle for the CAD Net window
    monitor_handle = MonitorFromWindow(cadnet_handle, MONITOR_DEFAULTTOPRIMARY)
    # Retrieve the DPI for the monitor
    dpiX = ctypes.wintypes.UINT()
    dpiY = ctypes.wintypes.UINT()
    GetDpiForMonitor(monitor_handle, MDT_EFFECTIVE_DPI, ctypes.byref(dpiX), ctypes.byref(dpiY))
    # Calculate the scaling factor (assuming 96 DPI as standard scaling factor 1.0)
    scaling_factor = dpiX.value / 96.0
    print(f"CAD Net monitor scaling factor: {scaling_factor}")
    
    def find_column_midpoints(header, scaling_factor):
        clearanceClass_x = clearanceClass_y = None
        netComment_x = netComment_y = None
        accumulated_width = 0
        # Iterate through header items to find the correct columns and their midpoints
        for i in range(header.item_count()):
            column_text = header.get_column_text(i)
            column_rect = header.get_column_rectangle(i)
            column_width = int(column_rect.width() * scaling_factor)
            accumulated_width += column_width
            # Detect clearanceClass column
            if column_text == 'clearanceClass':  
                clearanceClass_x = header.rectangle().left + accumulated_width - (column_width // 2)
                clearanceClass_y = header.rectangle().height() // 2
                print("clearanceClass column found.")
                print(f"clearance class midpoint: x={clearanceClass_x}, y={clearanceClass_y}")
            # Detect netComment
            if column_text == 'netComment':  
                netComment_x = header.rectangle().left + accumulated_width - (column_width // 2)
                netComment_y = header.rectangle().height() // 2
                print("netComment column found.")
                print(f"net comment midpoint: x={netComment_x}, y={netComment_y}")
        return (clearanceClass_x, clearanceClass_y), (netComment_x, netComment_y)   
    
    # Find column midpoints
    (clearanceClass_x, clearanceClass_y), (netComment_x, netComment_y) = find_column_midpoints(header, scaling_factor)
    
    print("Inputting Risk Class.")
    for i in range(1, 5):
        # ClearanceClass column
        header.click_input(coords=(clearanceClass_x, clearanceClass_y))  # Click on clearance class search tab
        cadnet_win.type_keys('RC{}'.format(i))  # Key in RC
        if cadnet_win.ListView.item_count() == 0: #if there is no items in that risk class, pass to next risk class
            pass
        else:
            header.click_input(coords=(clearanceClass_x, int(clearanceClass_y - 10 * scaling_factor))) # Click on clearance class header tab
            cadnet_win.type_keys('^a')  # Control + A to select all
            # Input Risk Class
            cadnet_win.click_input(button='right')
            for _ in range(6):
                cadnet_win.type_keys('{DOWN}')
            cadnet_win.type_keys('{RIGHT}')
            for _ in range(i):
                cadnet_win.type_keys('{DOWN}')
            cadnet_win.type_keys('{ENTER}')
            header.click_input(coords=(clearanceClass_x, clearanceClass_y)) # Click on clearance class search tab
            cadnet_win.type_keys('{BACKSPACE}')
            sleep(1)
            
        # NetComment column
        header.click_input(coords=(netComment_x, netComment_y)) # Click on netComment search tab
        cadnet_win.type_keys('RC{}'.format(i))  # Key in RC
        if cadnet_win.ListView.item_count() == 0: #if there is no items in that risk class, pass to next risk class
            pass
        else:
            header.click_input(coords=(netComment_x, int(netComment_y - 10 * scaling_factor))) # Click on netComment header tab
            cadnet_win.type_keys('^a')  # Control + A to select all
            # Input Risk Class
            cadnet_win.click_input(button='right')
            for _ in range(6):
                cadnet_win.type_keys('{DOWN}')
            cadnet_win.type_keys('{RIGHT}')
            for _ in range(i):
                cadnet_win.type_keys('{DOWN}')
            cadnet_win.type_keys('{ENTER}')
            header.click_input(coords=(netComment_x, netComment_y)) # Click on netComment search tab
            cadnet_win.type_keys('{BACKSPACE}')
            sleep(1)
    cadnet_win.close()
    print("Finish Risk Class Input.")
    sleep(3)
    
    #change directory to output directory
    os. chdir("C:\\CAx\\Prj")

    #Check if output file exits (if not, create file)
    #Check if file to store csv exits (if exists, delete and create new. if not, create)
    print("Create new file to store output files.")
    if os.path.exists("PCB CAM OUTPUT") == False:
        os.mkdir("PCB CAM OUTPUT")
        os.mkdir("PCB CAM OUTPUT/{}".format(file_name))
    else:
        if os.path.exists("PCB CAM OUTPUT/{}".format(file_name)) == True:
            shutil.rmtree("PCB CAM OUTPUT/{}".format(file_name))
            os.mkdir("PCB CAM OUTPUT/{}".format(file_name))
        else:
            os.mkdir("PCB CAM OUTPUT/{}".format(file_name))

    #Open Reliability check
    window.set_focus()
    window.Analysis.click_input()
    window.type_keys('{DOWN 9}{ENTER}')

    #Detect reliability check popup and click start
    sleep(3)
    print("Open Reliability Check.")
    check_rel_handle = pywinauto.findwindows.find_windows(title_re="Reliability Check")
    app3 = Application().connect(handle=check_rel_handle[0])
    check_rel_win = app3.window(handle=check_rel_handle[0])
    check_rel_win.Start.click_input()

    #Connect to Check results window and export Reliability-TOP csv
    sleep(5)
    check_results = pywinauto.findwindows.find_windows(title_re="Check Results")
    app4 = Application().connect(handle=check_results[0])
    check_results_win = app4.window(handle=check_results[0])
    check_results_win.ListView.select(0).click_input(double=True)
    # Get the current mouse position
    cursor_position = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(cursor_position))


    check_results_win.child_window(title="Draw All Errors", auto_id="cbDrawAllErrors", control_type="System.Windows.Forms.CheckBox").click_input()
    check_results_win.minimize()

    print("Take PCB top screenshot.")
    window.type_keys('^d') #set to default view (no zoom)
    window.set_focus()
    os.mkdir("PCB CAM OUTPUT/{}/Top_View".format(file_name)) #create new folder to store top images
    window['comp_+_top'].click_input() #click to display components view
    sleep(2)
    im_top_comp=ImageGrab.grab() #take screenshot
    im_top_comp.save('PCB CAM OUTPUT/{}/Top_View/{}_comp_+_top.png'.format(file_name,file_name)) #store screenshot

    window['comp_+_top'].click_input() #click to remove components view
    window.set_focus()
    sleep(2)
    im_top=ImageGrab.grab() #take screenshot
    im_top.save('PCB CAM OUTPUT/{}/Top_View/{}_top.png'.format(file_name,file_name)) #save screenshot

    #hover to column to right click and export
    check_results_win.set_focus()
    check_results_win['HeaderErrortype'].click_input(button='right')
    check_results_win.type_keys('{DOWN 3}{ENTER}')

    #Save Reliability-top csv
    sleep(5)
    print("Export PCB Top CLimate Risk csv.")
    export = pywinauto.findwindows.find_windows(title_re="Export list to")
    app5 = Application().connect(handle=export[0])
    export_win = app5.window(handle=export[0])

    #Edit address bar to correct directory (Prj/PCB CAM OUTPUT/odb file name)
    export_win.child_window(class_name="ToolbarWindow32", found_index=3).click_input(button='right')
    export_win.type_keys('{DOWN 3}{ENTER}')
    export_win.type_keys('C:/CAx/Prj/PCB CAM OUTPUT/{}'.format(file_name), with_spaces=True)
    export_win.type_keys('{ENTER}')
    export_win.Edit.type_keys('{}_top.csv'.format(file_name), with_spaces=True)
    export_win.Save.click_input()

    #Do the same for Reliability_BOT csv
    check_results_win.set_focus()
    double_click(button='left', coords=(cursor_position.x, int(cursor_position.y + (25*scaling_factor))))#move mouse down from reliability-top row
    check_results_win['HeaderErrortype'].click_input(button='right')
    check_results_win.type_keys('{DOWN 3}{ENTER}')

    #Same change as the top csv, but this time save as bot.csv
    sleep(3)
    print("Export PCB Bot CLimate Risk csv.")
    export = pywinauto.findwindows.find_windows(title_re="Export list to")
    app5 = Application().connect(handle=export[0])
    export_win = app5.window(handle=export[0])
    export_win.set_focus()
    export_win.child_window(class_name="ToolbarWindow32", found_index=3).click_input(button='right')
    export_win.type_keys('{DOWN 3}{ENTER}')

    export_win.type_keys('C:/CAx/Prj/PCB CAM OUTPUT/{}'.format(file_name), with_spaces=True)
    export_win.type_keys('{ENTER}')
    export_win.Edit.type_keys('{}_bot.csv'.format(file_name), with_spaces=True)
    export_win.Save.click_input()

    #minimize for screenshot
    sleep(3)
    check_results_win.set_focus()
    check_results_win.minimize()

    #take screenshot for bot view, same process as top view but different path name
    print("Take PCB bottom screenshots.")
    window.set_focus()
    os.mkdir("PCB CAM OUTPUT/{}/Bot_View".format(file_name))
    window['comp_+_bot'].click_input()
    sleep(2)
    im_bot_comp=ImageGrab.grab()
    im_bot_comp = im_bot_comp.transpose(Image.FLIP_LEFT_RIGHT)
    im_bot_comp.save('PCB CAM OUTPUT/{}/Bot_View/{}_comp_+_bot.png'.format(file_name,file_name))

    window['comp_+_bot'].click_input()
    window.set_focus()
    sleep(2)
    im_bot=ImageGrab.grab()
    im_bot = im_bot.transpose(Image.FLIP_LEFT_RIGHT)
    im_bot.save('PCB CAM OUTPUT/{}/Bot_View/{}_bot.png'.format(file_name,file_name))

    sleep(2)

    #import top csv to dataframe
    print("Combine PCB top and bottom CSV into one file.")
    top_df =  pd.read_csv('PCB CAM OUTPUT/{}/{}_top.csv'.format(file_name,file_name),  sep=';', engine='python', encoding= 'unicode_escape', )

    #format info column based on given value
    top_df.loc[top_df["Given Value"] == "200 µm", "Info"] = "RC0"
    top_df.loc[top_df["Given Value"] == "400 µm", "Info"] = "RC1"
    top_df.loc[top_df["Given Value"] == "600 µm", "Info"] = "RC2"
    top_df.loc[top_df["Given Value"] == "800 µm", "Info"] = "RC3"
    top_df.loc[top_df["Given Value"] == "1000 µm", "Info"] = "RC4"

    #remove row if value = given value
    top_df = top_df[top_df["Value"] != top_df["Given Value"]]

    # #import bot csv to dataframe
    bot_df =  pd.read_csv('PCB CAM OUTPUT/{}/{}_bot.csv'.format(file_name,file_name),  sep=';', engine='python', encoding= 'unicode_escape', )

    #format info column based on given value
    bot_df.loc[bot_df["Given Value"] == "200 µm", "Info"] = "RC0"
    bot_df.loc[bot_df["Given Value"] == "400 µm", "Info"] = "RC1"
    bot_df.loc[bot_df["Given Value"] == "600 µm", "Info"] = "RC2"
    bot_df.loc[bot_df["Given Value"] == "800 µm", "Info"] = "RC3"
    bot_df.loc[bot_df["Given Value"] == "1000 µm", "Info"] = "RC4"

    #remove row if value = given value
    bot_df = bot_df[bot_df["Value"] != bot_df["Given Value"]]

    #create new excel sheet to store dataframes
    new_wb = pd.ExcelWriter('PCB CAM OUTPUT/{}/{}.xlsx'.format(file_name,file_name), engine='xlsxwriter')

    #store top dateframe into worksheet name 'Top Reliabilty Check'
    top_df.to_excel(new_wb, sheet_name='Top Reliabilty Check', index=False)
    new_wb.sheets['Top Reliabilty Check'].autofilter(0, 0, top_df.shape[0], top_df.shape[1]-1)
    #store bot dateframe into worksheet name 'Bot Reliabilty Check'
    bot_df.to_excel(new_wb, sheet_name='Bot Reliabilty Check', index=False)
    new_wb.sheets['Bot Reliabilty Check'].autofilter(0, 0, bot_df.shape[0], bot_df.shape[1]-1)

    #save and close workbook
    print("Files combined.")
    new_wb.close()

    #kill excel application
    os.system('TASKKILL /F /IM excel.exe')

    sleep(2)

    #remove old csv files
    print("Remove old csv files.")
    os.remove('PCB CAM OUTPUT/{}/{}_top.csv'.format(file_name,file_name))
    os.remove('PCB CAM OUTPUT/{}/{}_bot.csv'.format(file_name,file_name))
    
    print("Program run successfull.")
    check_results_win.minimize()
    window.minimize()

    # Create and configure the Tkinter root window
    root = tk.Tk()
    root.withdraw() 
    root.lift() 
    root.attributes('-topmost', True) 
    root.focus_force()  # Force focus on the root window
    answer = askyesno(title='Confirmation', message='Do you want to close PCB CAM?', parent=root) #show message to user
    
    if answer:
        os.system('TASKKILL /F /IM PCB-CAM-Tool.exe')

    # Filepath to display on popup
    output = "C:/CAx/Prj/PCB CAM OUTPUT/{}/{}.xlsx".format(file_name, file_name)
    
    root.destroy()  # Destroy the root window after the message box is closed
    return output

#function to enable file explorer to open using button click and store filepath of odb
def open_file():
    filetypes = (
        ('All files', '*.*'),
        ('text files', '*.txt')
    )

    #file explorer opens
    path = fd.askopenfilename(
        title='Open a file',
        initialdir='/',
        filetypes=filetypes)

    #if file explorer is closed
    if path == '':
        #pop up: no file selected
        showinfo(
        title='Error',
        message= 'Please select file.'
    )
    else: #when file is selected
        #pop up: running script
        showinfo(
        title='Selected File',
        message= 'Loading file: {}\n\nDo not move mouse or touch keyboard.'.format(path)
    )
        #calls function that runs script
        output_path = pcb_run(path)
    
        #popup after finish script
        showinfo(
            title='Output',
            message= 'Output Excel location:\n{}'.format(output_path)
        )

##below is commented out because when converted to exe using pyinstaller, exe file will open again when you close it
# if __name__ == '__main__':
#     pcb_cam_auto.start_up()




