from datetime import datetime
from Version1.View import View
from Version1.Model import Model, BLOCK_SIZE_IDX, PATH_IDX, IS_FAST_IDX, MIN_SIZE_IDX, human_bytes
import threading
import time
from tkinter import END


UPDATE_SIZE_INTERVAL = 1  # In seconds

class Controller:
    def __init__(self):
        self.view = View(self)
        self.model = None

    def start_program(self):
        self.view.start_view()

    def update_gui(self, results_tb, tree_size_str, time_str):
        def update_gui_thread():
            scan_results = self.model.get_scan_results()
            # After the scan is done the report consists of 3 parts:

            # 1. The duplicate files groups
            results_tb.insert(END, scan_results.duplicates)

            # 2. Problems that were in the scan
            results_tb.insert(END, scan_results.problems)

            # 3. Ignored file (size is lower then set min size
            results_tb.insert(END, scan_results.ignored_files)

            # Update the time of the end of the scan
            time_str.set(time_str.get() + ", End time " + datetime.now().strftime('%H:%M:%S'))

        def update_total_size_thread():
            while not self.model.done_size_calc:
                tree_size_str.set("Total scanned size (still counting): " + human_bytes(self.model.total_size))
                time.sleep(UPDATE_SIZE_INTERVAL)
            tree_size_str.set("Total scanned size: " + human_bytes(self.model.total_size))

        # Calculate the size of the tree
        # Set a thread to update in a time interval the GUI with the currently calculated size
        threading.Thread(target=update_total_size_thread).start()

        threading.Thread(target=update_gui_thread).start()

    def start_scan_thread(self):
        # Reset the GUI in case there already was a scan
        self.view.reset_results_gui()

        scan_params = self.view.get_scan_params()

        # Initialize the object of the scan with all the params from the GUI
        self.model = Model(block_size=scan_params[BLOCK_SIZE_IDX],
                           path=scan_params[PATH_IDX],
                           is_fast_mode=scan_params[IS_FAST_IDX],
                           min_size=scan_params[MIN_SIZE_IDX])

        # Prepare the GUI and get the references of vars that show the data in the GUI
        results_tb, tree_size, time_str = self.view.prepare_gui_get_ref()
        self.update_gui(results_tb, tree_size, time_str)
