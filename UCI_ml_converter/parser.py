from dataclasses import dataclass
import sys
import os
from datafile import DataFile


@dataclass
class Parser:
    """
    Represent parser for user input passed via command line.
    """
    user_input: list[str]
    
    def process_arguments(self):
        """
        Processes command line arguments into list of Datafile objects
    
        :returns: DataFile object with all arguments to be used in later commands
        :rtype: DataFile
        """
        if self.user_input[1] == "-H":
            self._print_help()
            sys.exit()
        try:
            include_header = bool(int(self.user_input[1]))
            class_col = int(self.user_input[2]) if self.user_input[2] else -1
            ignore_cols = list(map(int, self.user_input[3].split(','))) if self.user_input[3] else []
            file_start, optional_params = self._process_flags(self.user_input[4:])

            if (optional_params["cls_drop"] or optional_params["custom_cls"]) and class_col != -1:
                print("Error: Can not specify both a class column and custom class to insert.")

            input_files, merge_files = self._get_files(self.user_input[file_start + 4:])

            extensions = list(map(self._get_file_extension, input_files))

            datafile_list = [DataFile(file_path=input_files[i], file_type=extensions[i], class_col_index=class_col,
                                      ignore_cols=ignore_cols, drop_cols = optional_params["drop_columns"], ignore_rows=optional_params["ignore_rows"],
                                      drop_footer=optional_params["drop_footer"], include_header=include_header if i == 0 else False,
                                      class_drop_chars=optional_params["cls_drop"], custom_class=optional_params["custom_cls"],
                                      merge_class=optional_params["merge_cls"], infer_non_num=optional_params["infer_non_num"])
                             for i in range(len(input_files))]
            
            for file_path, merge_paths in merge_files.items():
                for i in range(len(merge_paths)):
                    merge_files[file_path][i] = DataFile(merge_paths[i], *[None] * 9)

            return datafile_list, merge_files, optional_params["delay_write"]
        except IndexError:
            print("Error: Incorrect number of arguments passed.")
            self._print_help()
        

    def _get_file_extension(self, file_path: str) -> str:
        """
        Returns file extension of said file, taking the file path as an argument

        :param str file_path: path of a file
        :returns: file extension
        :rtype: str
        """
        try:
            return os.path.splitext(file_path)[-1]
        except ValueError:
            print("Error: Function argument must be a file path. Retry again.")


    def _get_files(self, input_paths: list[str]) -> tuple[list[str], dict[str: list[str]]]:
        """
        Return actual data files given a combination of files and/or folders, and drop non
        data files as specified by the user.
        """
        state = "ADD"
        input_files = []
        merge_files = {}
        for input_path in input_paths:
            if input_path == "-rm":
                state = "DROP"
                continue
            if input_path == "--merge":
                state = "MERGE"
                merge_files[input_files[-1]] = []
                continue
            if state == "ADD" and os.path.isfile(input_path):
                input_files.append(input_path)
            elif state == "MERGE":
                merge_files[input_files[-1]].append(input_path) 
            elif state == "DROP" and input_path[0] == "*":
                for filepath in set(input_files):
                    if os.path.basename(filepath) == input_path[1:]:
                        input_files.remove(filepath)
            elif state == "DROP":
                try:
                    input_files.remove(input_path)
                except KeyError:
                    print("Error: Can not remove nonexistent file.")
                    sys.exit()
            else:
                for root, dirs, files in os.walk(input_path):
                    for file in files:
                        input_files.append(os.path.join(root, file))
    
        return input_files, merge_files


    def _process_flags(self, user_input: list[str]) -> tuple[int, dict]:
        """
        Parse arguments for the following optional flags: -d, -cls, -clsd, --delay_write,
        --drop_col, --merge_cls.
        """
        flags = ["-d", "-db", "-cls", "-clsd", "--delay_write", "--drop_col", "--merge_cls", "--infer_nn"]
        optional_params = {"ignore_rows": 0, "drop_footer": 0, "cls_drop": False, "custom_cls": [],
                           "delay_write": False, "drop_columns": [], "merge_cls": [], "infer_non_num": False}
        i = 0
        while user_input[i] in flags:
            if user_input[i] == "-d":
                optional_params["ignore_rows"] = int(user_input[i + 1])
                increment = 2
            elif user_input[i] == "-db":
                optional_params["drop_footer"] = int(user_input[i + 1])
                increment = 2
            elif user_input[i] == "-clsd":
                optional_params["cls_drop"] = True
                optional_params["custom_cls"] = user_input[i + 1].split(",")
                increment = 2
            elif user_input[i] == "-cls":
                optional_params["custom_cls"].append(user_input[i + 1])
                increment = 2
            elif user_input[i] == "--delay_write":
                optional_params["delay_write"] = True
                increment = 1
            elif user_input[i] == "--drop_col":
                optional_params["drop_columns"] = list(map(int, user_input[i + 1].split(",")))
                increment = 2
            elif user_input[i] == "--merge_cls":
                optional_params["merge_cls"] = list(map(int, user_input[i + 1].split(",")))
                increment = 2
            elif user_input[i] == "--infer_nn":
                optional_params["infer_non_num"] = True
                increment = 1
            i += increment
    
        return i, optional_params


    def _print_help(self) -> None:
        help_format = "\t{:<25}{}"
        print("python UCI_ml_copy.py [-H] include_header class_col ignore_cols [-d rows] [-cls custom_class] [-clsd drop_chars] input_file(s)/folder(s) [-rm file(s)]")
        print(help_format.format("-H", "Optional. Prints the usage statement. All other arguments are ignored."))
        print(help_format.format("include_header", "Integer. If 1, add header if not already in dataset. If 0, drop header if dataset has one."))
        print(help_format.format("class_col", "Integer. The index of the classification column."))
        print(help_format.format("ignore_col(s)", "Integer(s). A list of indexes seperated by comma. Ex. '0,1,2,3,4,5,6'."))
        print(help_format.format("-d rows", "Optional. Integer. Drop the specified number of rows from the beginning of the file."))
        print(help_format.format("-cls custom_class", "Optional. String. Custom class name for all rows of input file(s)."))
        print(help_format.format("-clsd drop_chars", "Optional. String(s) separated by comma. Class name retrieved from file name with corresponding characters dropped. "\
        "Prepending/appending a * to the front/back of drop_chars indicates to drop all characters before\after drop_chars, "\
        "including drop_chars."))
        print(help_format.format("input_file(s)/folder(s)", "File/folder paths. The remaining arguments are paths to files/folders. Invalid file paths are ignored."))
        print(help_format.format("-rm file(s)", "Optional. File paths or *filename. Drop files that match the provided file path or all files that match "\
        "the filename."))