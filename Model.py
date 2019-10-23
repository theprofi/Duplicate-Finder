import os
import xxhash
from pathlib import Path
from collections import defaultdict


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

        # Get the only the duplicates
        groups_counter = 0
        duplicates = "========= Duplicates =========\n"
        for k in self.__results:
            if type(self.__results[k]) is defaultdict:
                for inner_k in self.__results[k]:
                    if len(self.__results[k][inner_k]) > 1:
                        groups_counter += 1
                        file_size_in_group = os.path.getsize(self.__results[k][inner_k][0])
                        duplicates += "- Identical files group #{}, each file size: {} ({} bytes)" \
                                          .format(groups_counter, human_bytes(file_size_in_group), file_size_in_group) \
                                      + "\n\t" + "\n\t".join(list(self.__results[k][inner_k])) + "\n\n"
        if len(duplicates) == 0:
            duplicates += "No duplicates found\n\n"

        problems = "========= Problems ========= \n"
        for k in self.__scan_exceptions:
            problems += "{} - {}\n".format(k, self.__scan_exceptions[k])
        if len(self.__scan_exceptions) == 0:
            problems += "No problems \n"

        ignored_files = "\n========= Ignored files (smaller than min size) ========= \n"
        for path in self.__ignored_files:
            ignored_files += str(path.absolute()) + "\n"
        if len(self.__ignored_files) == 0:
            ignored_files += "No ignored files\n"

        return ScanResultsAsString(duplicates=duplicates, problems=problems, ignored_files=ignored_files)

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


class ScanResultsAsString(object):
    def __init__(self, duplicates, problems, ignored_files):
        self.duplicates = duplicates
        self.problems = problems
        self.ignored_files = ignored_files
