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
        self.block_size = block_size
        self.path = Path(path)
        self.min_size = min_size
        self.hasher = xxhash.xxh32() if is_fast_mode else xxhash.xxh64()
        self.results = {}
        self.scan_exceptions = {}
        self.ignored_files = []
        self.total_size = 0
        self.done_size_calc = False

    def get_duplicates(self):
        self._start_duplicates_scan()
        duplicate_ls = []
        for k in self.results:
            if type(self.results[k]) is defaultdict:
                for inner_k in self.results[k]:
                    if len(self.results[k][inner_k]) > 1:
                        duplicate_ls.append([os.path.getsize(self.results[k][inner_k][0])] +
                                            list(self.results[k][inner_k]))
        return duplicate_ls

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
                self.scan_exceptions["General problem"] = "The path doesn't exist"
                return False
            if not self.path.is_absolute():
                self.scan_exceptions["General problem"] = "The path is absolute"
                return False
            if not self.path.is_dir():
                self.scan_exceptions["General problem"] = "The path is not a directory"
                return False
            return True

        def block_size_check_save_error():
            try:
                self.block_size = int(self.block_size)
            except:
                self.scan_exceptions["General problem"] = "The block size is not a positive integer"
                return False
            if self.block_size <= 0:
                self.scan_exceptions["General problem"] = "The block size is not a positive integer"
                return False
            return True

        def min_size_check_save_error():
            try:
                self.min_size = int(self.min_size)
            except:
                self.scan_exceptions["General problem"] = "The min size is not a positive integer or zero"
                return False
            if self.min_size < 0:
                self.scan_exceptions["General problem"] = "The block size is not a positive integer"
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
                        self.ignored_files.append(cur_file_path)
                        continue
                    self.total_size += cur_file_size
                    if cur_file_size not in self.results:
                        self.results[cur_file_size] = cur_file_path
                    elif type(self.results[cur_file_size]) is not defaultdict:
                        prev_file_path = self.results[cur_file_size]
                        self.results[cur_file_size] = defaultdict(lambda: [])
                        self.results[cur_file_size][self.get_hash(prev_file_path)].append(str(prev_file_path))
                        self.results[cur_file_size][self.get_hash(cur_file_path)].append(str(cur_file_path))
                    else:
                        cur_file_hash = self.get_hash(cur_file_path)
                        self.results[cur_file_size][cur_file_hash] = self.results[cur_file_size].get(cur_file_hash, [])
                        self.results[cur_file_size][cur_file_hash].append(str(cur_file_path))
                except OverflowError:
                    self.scan_exceptions.clear()
                    self.scan_exceptions["General error"] = "Block size is too large"
                    return
                except Exception as e:
                    self.scan_exceptions[cur_file_path] = e
        self.done_size_calc = True
