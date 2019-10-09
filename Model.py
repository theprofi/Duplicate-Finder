import os
import xxhash
from pathlib import Path
from collections import defaultdict

BLOCK_SIZE_IDX = 0
PATH_IDX = 1
IS_FAST_IDX = 2
MIN_SIZE_IDX = 3


class Model:
    def __init__(self, block_size, path, is_fast_mode, min_size=0):
        # The parameters from the GUI
        self.block_size = block_size
        self.path = Path(path)
        self.min_size = min_size
        self.hasher = xxhash.xxh32() if is_fast_mode else xxhash.xxh64()

        # The rest
        self.total_size = 0
        self.done_size_calc = False
        self.__results = {}
        self.__scan_exceptions = {}
        self.__ignored_files = []

    def get_scan_results(self):
        # Start the scan
        self._start_duplicates_scan()
        results = ScanResult()

        # Get the only the duplicates
        for k in self.__results:
            if type(self.__results[k]) is defaultdict:
                for inner_k in self.__results[k]:
                    if len(self.__results[k][inner_k]) > 1:
                        file_size_in_group = os.path.getsize(self.__results[k][inner_k][0])
                        results.add_list(files_list=list(self.__results[k][inner_k]), size=file_size_in_group)

        for k in self.__scan_exceptions:
            results.problems.append("{} - {}\n".format(k, self.__scan_exceptions[k]))

        for path in self.__ignored_files:
            results.ignored_files.append(str(path.absolute()) + "\n")

        return results

    def get_hash(self, file_path):
        self.hasher.reset()
        with open(file_path, "rb") as f:
            while True:
                buf = f.read(self.block_size)
                if not buf:
                    break
                self.hasher.update(buf)
        return self.hasher.hexdigest()

    def __initial_params_check_save_errors(self):
        def path_check_save_error():
            if not self.path.exists():
                self.__scan_exceptions["General problem"] = "The path doesn't exist"
                return False
            if not self.path.is_absolute():
                self.__scan_exceptions["General problem"] = "The path is absolute"
                return False
            if not self.path.is_dir():
                self.__scan_exceptions["General problem"] = "The path is not a directory"
                return False
            return True

        def block_size_check_save_error():
            try:
                self.block_size = int(self.block_size)
            except:
                self.__scan_exceptions["General problem"] = "The block size is not a positive integer"
                return False
            if self.block_size <= 0:
                self.__scan_exceptions["General problem"] = "The block size is not a positive integer"
                return False
            return True

        def min_size_check_save_error():
            try:
                self.min_size = int(self.min_size)
            except:
                self.__scan_exceptions["General problem"] = "The min size is not a positive integer or zero"
                return False
            if self.min_size < 0:
                self.__scan_exceptions["General problem"] = "The block size is not a positive integer"
                return False
            return True

        return path_check_save_error() and block_size_check_save_error() and min_size_check_save_error()

    def _start_duplicates_scan(self):
        if not self.__initial_params_check_save_errors():
            return
        for dir_path, dir_names, file_names in os.walk(self.path):
            for f in file_names:
                cur_file_path = Path(dir_path, f)
                try:
                    cur_file_size = os.path.getsize(cur_file_path)
                    if cur_file_size < self.min_size:
                        self.__ignored_files.append(cur_file_path)
                        continue
                    self.total_size += cur_file_size
                    if cur_file_size not in self.__results:
                        self.__results[cur_file_size] = cur_file_path
                    elif type(self.__results[cur_file_size]) is not defaultdict:
                        prev_file_path = self.__results[cur_file_size]
                        self.__results[cur_file_size] = defaultdict(lambda: [])
                        self.__results[cur_file_size][self.get_hash(prev_file_path)].append(str(prev_file_path))
                        self.__results[cur_file_size][self.get_hash(cur_file_path)].append(str(cur_file_path))
                    else:
                        cur_file_hash = self.get_hash(cur_file_path)
                        self.__results[cur_file_size][cur_file_hash] = self.__results[cur_file_size].get(cur_file_hash,
                                                                                                         [])
                        self.__results[cur_file_size][cur_file_hash].append(str(cur_file_path))
                except OverflowError:
                    self.__scan_exceptions.clear()
                    self.__scan_exceptions["General error"] = "Block size is too large"
                    return
                except Exception as e:
                    self.__scan_exceptions[cur_file_path] = e
        self.done_size_calc = True


class ScanResult(object):
    def __init__(self):
        self.duplicates = []
        self.problems = []
        self.ignored_files = []

    def add_list(self, files_list, size):
        self.duplicates.append((files_list, size))
