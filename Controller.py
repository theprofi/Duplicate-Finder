from datetime import datetime
from Version1.View import View
from Version1.Model import Model, BLOCK_SIZE_IDX, PATH_IDX, IS_FAST_IDX, MIN_SIZE_IDX
import threading
import time
from tkinter import END


UPDATE_SIZE_INTERVAL = 1  # In seconds


def human_bytes(b):
    """
    Return the given bytes as a human friendly KB, MB, GB, or TB string.
    :param b: bytes
    :return: string of human readable unit
    """
    b = float(b)
    kb = float(1024)
    mb = float(kb ** 2)  # 1,048,576
    gb = float(kb ** 3)  # 1,073,741,824
    tb = float(kb ** 4)  # 1,099,511,627,776

    if b < kb:
        return '{0} {1}'.format(b, 'Bytes' if 0 == b > 1 else 'Byte')
    elif kb <= b < mb:
        return '{0:.2f} KB'.format(b / kb)
    elif mb <= b < gb:
        return '{0:.2f} MB'.format(b / mb)
    elif gb <= b < tb:
        return '{0:.2f} GB'.format(b / gb)
    elif tb <= b:
        return '{0:.2f} TB'.format(b / tb)


class Controller:
    def __init__(self):
        self.view = View(self)
        self.model = None

    def start_program(self):
        self.view.start_view()

    def update_gui(self, results_tb, tree_size_str, time_str):
        def update_gui_thread():
            duplicate_files_groups = self.model.get_duplicates()
            # After the scan is done the report consists of 3 parts:
            # 1. The duplicate files groups
            for i, group in enumerate(duplicate_files_groups):
                results_tb.insert(END, "========= Identical files group #{}, each file size: {} bytes"
                                  .format(i + 1, group[0]) +
                                  " ========= \n" + "\n".join(group[1:]) + "\n\n\n")
            if len(duplicate_files_groups) == 0:
                results_tb.insert(END, "========= No duplicates found =========\n\n")

            # 2. Problems that were in the scan
            results_tb.insert(END, "========= Problems ========= \n")
            for k in self.model.scan_exceptions:
                results_tb.insert(END, "{} - {}\n".format(k, self.model.scan_exceptions[k]))
            if len(self.model.scan_exceptions) == 0:
                results_tb.insert(END, "No problems \n")

            # 3. Ignored file (size is lower then set min size
            results_tb.insert(END, "\n========= Ignored files (smaller than min size) ========= \n")
            if len(self.model.ignored_files) > 0:
                for path in self.model.ignored_files:
                    results_tb.insert(END, str(path.absolute()) + "\n")
            else:
                results_tb.insert(END, "No ignored files \n")

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
