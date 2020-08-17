#!/usr/bin/env python3
#   Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License").
#   You may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

'''
This module contains classes and functions related to building the arpa internal representation
'''

import os
import json
import logging
import sys
import subprocess
import re
import tempfile
import voluptuous
import voluptuous.humanize
import lib.arpa_helper as helper
#TODO add the import in method to allow running without validation


class CompileCommands:
    ''' Class that contains an internal representation of the input compile commands '''

    def __init__(self, cc_path):
        self.path = cc_path
        self.__validate()
        self.file_2_command = {}

    def __validate(self):
        if not os.path.exists(self.path):
            logging.error("Specified path does not point to an existing file: %s", self.path)
            sys.exit(1)

    def create_file_2_command_map(self):
        ''' create a map between files in the code base and the correspoding compile command '''
        with open(self.path, "r") as handle:
            all_commands = json.load(handle)

        for compilation_command in all_commands:
            cc_file = str(compilation_command['file'])
            cc_command = compilation_command['command'].split()
            self.file_2_command[cc_file] = cc_command

    @classmethod
    def __get_flag_arg(cls, flag, arg, next_arg):
        ''' if string corresponds to correct flag, return corresponding argument. '''
        if arg.startswith(flag):
            if len(arg) == len(flag):
                return next_arg
            if len(arg) > len(flag):
                return arg[len(flag):]
        else:
            return None

    def __get_abspath(self, include):
        '''transform included path to an absolute path '''
        if os.path.isabs(include) and os.path.exists(include):
            return include
        path = os.path.join(os.path.dirname(self.path), include)
        if os.path.exists(path):
            return os.path.abspath(path)

        logging.error("include path not found at %s", path)
        sys.exit(1)

    def __get_flags(self, prefix, file):
        command_split = self.file_2_command[file]
        all_flags = []
        for command_tuple in enumerate(command_split):
            cmd_ind = command_tuple[0]
            next_arg = "" if cmd_ind == len(command_split)-1 else command_split[cmd_ind+1]
            flag = self.__get_flag_arg(prefix, command_split[cmd_ind], next_arg)
            if flag:
                all_flags.append(flag)

        return all_flags

    def get_includes(self, file):
        ''' return included directories (from the compile command) for a given file '''
        all_includes = self.__get_flags(helper.CC_INCLUDE, file)
        all_includes_absolute = []
        for include_path in all_includes:
            all_includes_absolute.append(self.__get_abspath(include_path))
        return all_includes_absolute

    def get_defines(self, file):
        ''' return cmd line defines (from the compile command) for a given file '''
        return self.__get_flags(helper.CC_DEFINE, file)

    # TODO handle other flags from the compilation commands, put them in CFLAGS


class InternalRepresentation:
    ''' Class that defines an internal representation containing all build information
    for a given code base '''

    def __init__(self, root_path):
        self.representation = {helper.JSON_INFO: root_path,
                               helper.JSON_FILE: {}, }

    def __add_element(self, file_path, key, value):
        self.representation[helper.JSON_FILE][file_path][key] = value

    def add_file_entry(self, file_path):
        ''' add file as key in internal_rep '''
        file_name = os.path.basename(file_path)
        if file_path in self.representation[helper.JSON_FILE]:
            logging.warning("Clashing file name: %s", file_path)
        else:
            self.representation[helper.JSON_FILE][file_path] = {}
            self.__add_element(file_path, helper.JSON_NAME, file_name)

    def add_defines(self, file_path, defines_list):
        ''' add cmd line defines to internal_rep '''
        self.__add_element(file_path, helper.JSON_DEF, defines_list)

    def add_includes(self, file_path, includes_list):
        ''' add included dirs to internal_rep '''
        self.__add_element(file_path, helper.JSON_INC, includes_list)

    def add_dependencies(self, file_2_dependencies):
        ''' add fct=level dependencies to internal_rep '''
        for file in file_2_dependencies:
            if file in self.representation[helper.JSON_FILE]:
                self.representation[helper.JSON_FILE][file][helper.JSON_FCT] = \
                    file_2_dependencies[file]
            else:
                if file.endswith(".c"):
                    logging.info("source file <%s> not found"
                                 " in internal representation. Adding.", file)
                elif file.endswith(".h"):
                    logging.debug("Header <%s> not found "
                                  "in internal representation. Adding.", file)
                else:
                    logging.error("<%s> not found in internal representation. Exiting.", file)
                    sys.exit(1)
                self.representation[helper.JSON_FILE][file] = {
                    helper.JSON_NAME: os.path.basename(file),
                    helper.JSON_INC: [],
                    helper.JSON_DEF: [],
                    helper.JSON_FCT: file_2_dependencies[file],
                }

        # TODO possibly remove?
        for file in self.representation[helper.JSON_FILE]:
            if file not in file_2_dependencies:
                self.representation[helper.JSON_FILE][file][helper.JSON_FCT] = {}


    def validate(self):
        ''' validate the internal representation using voluptuous '''
        def h_c_file(value):
            if isinstance(value, str) and (value.endswith(".c") or value.endswith(".h")):
                return value
            raise voluptuous.Invalid("Not an existing .c or .h file.")

        def existing_file(value):
            if isinstance(value, str) and os.path.isfile(value):
                return value
            raise voluptuous.Invalid("Not an existing file.")

        def existing_directory(value):
            if isinstance(value, str) and os.path.isdir(value):
                return value
            raise voluptuous.Invalid("Not an existing directory.")

        def compiler_define(value):
            regex = re.compile(r"\w+(=.+)?")
            if isinstance(value, str) and regex.match(value):
                return value
            raise voluptuous.Invalid("Not a valid compiler define.")

        def function_name(value):
            regex = re.compile(r"\w+")
            if isinstance(value, str) and regex.match(value):
                return value
            raise voluptuous.Invalid("Not a valid function name.")

        schema = voluptuous.Schema({
            helper.JSON_INFO: existing_directory,
            helper.JSON_FILE: {
                voluptuous.All(h_c_file, existing_file): {
                    helper.JSON_NAME: h_c_file,
                    helper.JSON_INC: [existing_directory],
                    helper.JSON_DEF: [compiler_define],
                    helper.JSON_FCT: {
                        function_name: {
                            function_name: voluptuous.Any(voluptuous.All(h_c_file, existing_file),
                                                          None)
                        }
                    }
                }
            }
        }, required=True)
        voluptuous.humanize.validate_with_humanized_errors(self.representation, schema)

    def write_to_file(self, path):
        ''' output a file continaing the json internal representation used in the tool '''
        outjson = json.dumps(self.representation, indent=4)
        with open(path, "w") as handle:
            print(outjson, file=handle)


class CflowInstance:
    ''' Class that encapsulates all the info in a given Cflow call '''

    def __init__(self):
        self.command = ["cflow"]
        self.file_2_dependencies = {}
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.output_path = temp_file.name
        temp_file.close()


    def __add_to_command(self, item):
        self.command.append(item)

    @classmethod
    def __find_h_and_c(cls, root_dir):
        '''From the project root, return a list of all header and source files in the project'''
        all_h_and_c = []
        exclude = ["aws-proof-build-assistant"]
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in exclude]
            for file in files:
                if file.endswith(".h") or file.endswith(".c"):
                    f_path = os.path.abspath(os.path.join(root, file))
                    all_h_and_c.append(f_path)
        return all_h_and_c

    def init_command(self, root_path):
        ''' initialize the cflow command'''
        h_and_c_files = self.__find_h_and_c(root_path)
        self.command.extend(h_and_c_files)
        self.command.extend(["-A", "--no-main", "-o%s" %(self.output_path), "--brief"])

    def run_command(self):
        ''' run the cflow command '''
        proc = subprocess.Popen(self.command, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, universal_newlines=True)
        _, errors = proc.communicate()
        for cflow_message in errors.split("\n"):
            logging.warning("cflow stderr > %s", cflow_message)

    def parse_output(self):
        '''parse cflow output file, integrate it into the file_2_dependencies field'''

        current_at_level = []
        with open(self.output_path, "r") as cflow_out:
            cnt = 0
            for cur_line in cflow_out:
                # get depth of current line
                leading_spaces = len(cur_line) - len(cur_line.lstrip(" "))
                cur_depth = leading_spaces // 4
                if leading_spaces % 4:
                    logging.warning("Line has %d leading spaces: %s", leading_spaces, cur_line[:-1])

                #add function to internal rep
                regex = (r"(?P<fct>\w+)\(\)"
                         r"( <.+ at (?P<file>.+):\d+>"
                         r"( (?P<rec>\(R\)))?:)?"
                         r"( \[see (?P<ref>\d+)\])?")
                match = re.match(regex, cur_line.strip())
                if not match:
                    logging.warning("Regex did not match for \"%s\"", cur_line[:-1])
                    continue

                cf_func = match["fct"]
                cf_file = match["file"]
                cf_ref = match["ref"]
                if cf_file and not cf_ref:
                    if cf_file in self.file_2_dependencies:
                        if cf_func in self.file_2_dependencies[cf_file]:
                            logging.warning("duplicate entry for %s in %s", cf_func,
                                            cf_file)
                        self.file_2_dependencies[cf_file][cf_func] = {}
                    else:
                        self.file_2_dependencies[cf_file] = {cf_func:{}}

                #handle function callings
                cur_node = (cf_func, cf_file)

                if cur_depth < len(current_at_level) - 1:
                    current_at_level = current_at_level[:cur_depth + 1]
                    current_at_level[cur_depth] = cur_node
                elif cur_depth == len(current_at_level) - 1:
                    current_at_level[cur_depth] = cur_node
                elif cur_depth == len(current_at_level):
                    current_at_level.append(cur_node)
                elif cur_depth > len(current_at_level):
                    logging.error("jump in depth at line %d", cnt)
                    sys.exit(1)

                if cur_depth != 0:
                    #add to 1 depth less
                    parent_depth = cur_depth - 1
                    parent_func = current_at_level[parent_depth][0]
                    parent_file = current_at_level[parent_depth][1]

                    if parent_file in self.file_2_dependencies:
                        self.file_2_dependencies[parent_file][parent_func][cf_func] = cf_file
                    else:
                        logging.error("Parent file %s of calling function %s of "
                                      "called function %s is not found in cflow output.",
                                      parent_file, parent_func, cf_func)
                        sys.exit(1)
                cnt += 1
