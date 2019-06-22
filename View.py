import time
from tkinter import filedialog
from Version1.Model import BLOCK_SIZE_IDX, PATH_IDX, IS_FAST_IDX, MIN_SIZE_IDX
from tkinter import *
import threading
from datetime import datetime


# Constants of the program
MIN_SCREEN_WIDTH = 750
DEFAULT_BLOCK_SIZE = 2 ** 10
BORDER_WIDTH_SETTINGS_FRAME = 11


class View:
    def __init__(self, controller):
        def init_first_frame():
            """
            Initialize the first frame that contains the settings for the scan.
            It has a one row grid with the middle column expandable (for the path input).
            :return: None
            """
            first_row_frame = Frame(self.main_frame)
            first_row_frame.pack(side=TOP, fill=BOTH)
            first_row_frame.grid_columnconfigure(1, weight=1)

            Label(first_row_frame, text="Start scanning from:", width=40, anchor=W).grid(row=0, column=0, sticky=W)

            path_label = Entry(first_row_frame, textvariable=self.path)
            path_label.grid(row=0, column=1, sticky=W + E)

            browse_btn = Button(first_row_frame, text="Browse",
                                command=lambda: self.path.set(filedialog.askdirectory()))
            browse_btn.grid(row=0, column=2, sticky=W, padx=(5, 5))

        def init_second_frame():
            """
            Initialize the second frame that contains the settings for the scan.
            This frame has 3 lines. It contains the settings: min file size, fast/slow scan and block size.
            :return:
            """
            # This frame contains the middle rows with other scan settings
            other_rows_frame = Frame(self.main_frame)
            other_rows_frame.pack(anchor=W)

            # Second frame - second row of the settings and start button GUI
            Label(other_rows_frame, text="Ignore files smaller than:").grid(row=0, column=0, sticky=W)

            min_size_entry = Entry(other_rows_frame, width=15, textvariable=self.min_size)
            min_size_entry.grid(row=0, column=1, sticky=W)

            Label(other_rows_frame, text="bytes").grid(row=0, column=2, sticky=W)

            # Second frame - third row of the settings and start button GUI
            Label(other_rows_frame, text="Block size for hashing: ").grid(row=1, column=0, sticky=W)

            block_size_entry = Entry(other_rows_frame, width=15, textvariable=self.block_size)
            block_size_entry.grid(row=1, column=1, sticky=W)

            Label(other_rows_frame, text="bytes").grid(row=1, column=2, sticky=W)

            # Second frame - fourth row of the settings and start button GUI
            Label(other_rows_frame, text="Faster scan (more false positives) or slower scan:", width=40, anchor=W).grid(row=2, column=0, sticky=W)

            radio_is_fast_fast = Radiobutton(other_rows_frame, text="Fast", value=True, variable=self.is_fast)
            radio_is_fast_fast.grid(row=2, column=1, sticky=W)

            radio_is_fast_slow = Radiobutton(other_rows_frame, text="Slow", value=False, variable=self.is_fast)
            radio_is_fast_slow.grid(row=2, column=2, sticky=W)

        def init_third_frame():
            """
            This frame contains the last row, the one with with the start scan button.
            It's in a separate frame because we want the button to always stay in the middle of the width of the window,
            while the settings in the 2 other frames must always be fixed in the left side of the window.
            :return: None
            """
            last_row_frame = Frame(self.main_frame)
            last_row_frame.pack(expand=True, anchor=N)
            start_scan_btn = Button(last_row_frame, text="Start scan",
                                    command=lambda: self.controller.start_scan_thread())
            start_scan_btn.pack(pady=(5, 5))

        self.elements_to_remove = []
        self.controller = controller
        # The window of the program
        self.window = Tk()
        self.window.title("Kind Duplicate Finder")

        # The parameters of the scan that are determined in the GUI
        self.block_size = StringVar(self.window, DEFAULT_BLOCK_SIZE)
        self.path = StringVar(self.window, "")
        self.is_fast = BooleanVar(self.window, False)
        self.min_size = IntVar(self.window, 0)

        # The frame that contains all the GUI for starting and configuring the scan (the 3 frames below)
        self.main_frame = LabelFrame(bd=BORDER_WIDTH_SETTINGS_FRAME, relief=GROOVE, text="Config the scan")
        self.main_frame.pack(fill=X, anchor=N, pady=(5, 5), padx=(5, 5))

        # The 3 frames that contains the start button and the settings for the scan.
        # 1st frame has it's 2nd column of the grid expandable for the path input text box
        # 2nd frame's all data is fixed to the left side and doesn't change it's style
        # 3rd frame has one button that always in the center if the width of the window
        init_first_frame()
        init_second_frame()
        init_third_frame()

        # After the settings and start button GUI is ready, we know the height of the windows so we can set the min
        # height of the window accordingly
        self.__set_screen_min_dimensions()

    def __set_screen_min_dimensions(self):
        self.window.update()
        self.window.minsize(MIN_SCREEN_WIDTH, self.window.winfo_height())

    def get_scan_params(self):
        return [self.block_size.get(), self.path.get(), self.is_fast.get(), self.min_size.get()]

    def prepare_gui_get_ref(self):
        tree_size_str = StringVar(self.window, "")
        time_str = StringVar(self.window, "Scan start time: " + datetime.now().strftime('%H:%M:%S'))
        self.elements_to_remove.append(Label(self.window, textvariable=tree_size_str))
        self.elements_to_remove[-1].pack(anchor=N)

        self.elements_to_remove.append(Label(self.window, textvariable=time_str))
        self.elements_to_remove[-1].pack(anchor=N)

        self.elements_to_remove.append(Label(self.window, text="Results:\n"))
        self.elements_to_remove[-1].pack(anchor=N)

        # Configure a text box with a scroll bar
        self.elements_to_remove.append(Scrollbar(self.window))
        self.elements_to_remove[-1].pack(side=RIGHT, fill=Y, pady=(0, 5), anchor=N)

        results_tb = Text(wrap=WORD, yscrollcommand=self.elements_to_remove[-1].set, font=("consolas", 12))
        results_tb.pack(pady=(0, 5), fill=BOTH, expand=True)
        self.elements_to_remove[-1].config(command=results_tb.yview)

        self.elements_to_remove.append(results_tb)
        return results_tb, tree_size_str, time_str

    def reset_results_gui(self):
        for e in self.elements_to_remove:
            e.pack_forget()
        self.elements_to_remove.clear()

    def start_view(self):
        self.window.mainloop()
