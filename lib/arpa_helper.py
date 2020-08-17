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
This module contains helpful classes and functions used within Arpa
'''

import argparse
import os

TOOL_NAME = "arpa"

OUT_JSON_NAME = "internal_rep.json"
OUT_MF_NAME = "Makefile." + TOOL_NAME

JSON_INFO = "root"
JSON_FILE = "files"
JSON_NAME = "name"
JSON_INC = "includes"
JSON_DEF = "defines"
JSON_FCT = "functions"

CC_INCLUDE = "-I"
CC_DEFINE = "-D"


class FileSpecificInfo:
    ''' Class that finds and stores file-specific build info '''

    def __init__(self):
        self.includes = set()
        self.defines = set()
        self.dependencies = set()
        self.missing_dependencies = {}
        self.func_calls = {} # not currently used, but this may be useful going forward

    @classmethod
    def __change_extension(cls, path, ext):
        '''change the extension of a file given it's path'''
        name, _ = os.path.splitext(path)
        return "%s.%s" % (name, ext)

    def find_custom_info_recursively(self, change_dependency_extensions, internal_rep,
                                     current_path, relevant_functions):
        ''' recursively look for interesting information related to Makefile generation '''
        # Recursion issues are supposed to be handled by cflow
        current_json_entry = internal_rep[JSON_FILE][current_path]
        self.includes.update(set(current_json_entry[JSON_INC]))
        self.defines.update(set(current_json_entry[JSON_DEF]))

        file_2_called_functions = {}
        for fct in relevant_functions:
            for called_fct, called_file in current_json_entry[JSON_FCT][fct].items():
                if called_file:
                    # case where a file location is specified for the called function
                    called_file_w_ext = called_file
                    if change_dependency_extensions:
                        called_file_w_ext = \
                            self.__change_extension(called_file, change_dependency_extensions)
                    self.dependencies.add(called_file_w_ext)

                    # add called function to the list of recursive future calls
                    if called_file in file_2_called_functions:
                        file_2_called_functions[called_file].add(called_fct)
                    else:
                        file_2_called_functions[called_file] = {called_fct}

                    # map of which function calls which other function
                    if called_file in self.func_calls:
                        self.func_calls[called_file_w_ext].append(called_fct)
                    else:
                        self.func_calls[called_file_w_ext] = [called_fct]
                else:
                    #case where the location of a called fct is not known
                    entry = (current_path, fct)
                    if entry in self.missing_dependencies:
                        self.missing_dependencies[entry].add(called_fct)
                    else:
                        self.missing_dependencies[entry] = {called_fct}

        for file_path, file_functions in file_2_called_functions.items():
            self.find_custom_info_recursively(change_dependency_extensions,
                                              internal_rep, file_path, file_functions)


class ParserInstance:
    ''' Class that parses command line arguments'''

    def __init__(self, parent):
        self.parent = parent
        self.subparser = None
        self.bare_minimum_parser = None

    @classmethod
    def __create_bare_minimum_parser(cls):
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("-cc", "--compile-commands", required=True,
                            metavar="FILE",
                            help="path to compile_commands json file.")
        return parser


    def __create_build_parser(self):
        # default = called from project root directory
        parser = self.subparser.add_parser('build', parents=[self.bare_minimum_parser],
                                           help="Generate a JSON build database \
            for the current project and saves it to a file. Assumed cwd = project root.")

        # ADD FLAGS
        parser.add_argument("-r", "--root-dir", default=os.getcwd(),
                            metavar="DIR",
                            help="root directory for the project under test")
        parser.add_argument("-jp", "--json_path", default=OUT_JSON_NAME,
                            metavar="FILE",
                            help="output location for a file containing a json internal \
            representation of the stored information.")

        # ADD FUNCTION
        parser.set_defaults(func=self.parent.call_build)


    def __create_run_parser(self):
        # default = called from harness directory
        # TODO this subcommand should be changed to "makefile" instead of "run"
        parser = self.subparser.add_parser('run', parents=[self.bare_minimum_parser],
                                           help="Generate a Makefile from scratch \
            for a given harness file. Assumed cwd = harness directory.")

        # ADD FLAGS related to I/O
        parser.add_argument("-r", "--root-dir", required=True, metavar="DIR",
                            help="root directory for the project under test")
        parser.add_argument("-file", "--file-under-test", metavar="FILE",
                            help="path to harness for which we create a makefile.")
        parser.add_argument("-sp", "--save-path", metavar="FILE",
                            help="file path where the output Makefile will be saved")

        # ADD FLAGS related to PROOF ENTRY
        # parser.add_argument("-ef", "--entry-file", default="HARNESS_FILE",
        #                         metavar="V",
        #                         help="label for entry file used in the Makefile")
        # parser.add_argument("-en", "--entry-name", default="HARNESS_ENTRY",
        #                         metavar="V",
        #                         help="label for entry type used in the Makefile")
        # parser.add_argument("-sh", "--shorten-entry", action="store_true",
        #                         help="shorten harness name when writing entry")

        # ADD FLAGS related to BUILD INFO TYPES
        parser.add_argument("-def", "--define-variable", default="DEFINES",
                            metavar="V",
                            help="label for defines used in the Makefile")
        parser.add_argument("-inc", "--include-variable", default="INCLUDES",
                            metavar="V",
                            help="label for includes used in the Makefile")
        # parser.add_argument("-dep", "--dependency-variable", default="DEPENDENCIES",
        #                         metavar="V",
        #                         help="label for dependencies used in the Makefile")
        parser.add_argument("-ext", "--change-dependency-extensions",
                            metavar="EXT",
                            help="modify the extension of dependencies \
            in the generated Makefile")

        # ADD FLAGS related to MAKEFILE SRCDIR
        parser.add_argument("-mrv", "--make-root-variable", default="SRCDIR",
                            metavar="V",
                            help="Makefile variable name for root directory")
        parser.add_argument("-mrp", "--make-root-path", metavar="DIR",
                            help="path makefile real root directory")

        # ADD FLAGS related to MAKEFILE PROOF_SOURCES
        parser.add_argument("-msrv", "--make-proof-source-variable", default="PROOF_SOURCE",
                            metavar="V",
                            help="Makefile variable name for proofs directory")
        parser.add_argument("-msrp", "--make-proof-source-path", default="tests/cbmc/sources",
                            metavar="DIR",
                            help="path makefile proofs directory")

        # ADD FLAGS related to MAKEFILE PROOF_STUBS
        parser.add_argument("-mstv", "--make-proof-stub-variable", default="PROOF_STUB",
                            metavar="V",
                            help="Makefile variable name for proof stubs directory")
        parser.add_argument("-mstp", "--make-proof-stub-path", default="tests/cbmc/stubs",
                            metavar="DIR",
                            help="path makefile proof stubs directory")

        # ADD FLAGS related to MAKEFILE DEPENDENCY TYPES
        parser.add_argument("-mproj", "--make-project-sources-variable",
                            default="PROJECT_SOURCES",
                            metavar="V",
                            help="Makefile variable name for source file under test")
        parser.add_argument("-mproo", "--make-proof-sources-variable", default="PROOF_SOURCES",
                            metavar="V",
                            help="Makefile variable name for proofs source file")

        # # ADD FLAGS related to ...
        # parser.add_argument("-mpn", "--make-proofs-name", default="PROOFDIR",
        #                             metavar="V",
        #                             help="Makefile variable name for proofs directory")

        # ADD FUNCTION
        parser.set_defaults(func=self.parent.call_run)


    def parse_arguments(self):
        '''parse arguments'''
        # potentialTODO get inputs from JSON
        parser = argparse.ArgumentParser(description=__doc__)
        self.subparser = parser.add_subparsers(help="Available commands for \
            {}".format(TOOL_NAME))

        self.bare_minimum_parser = self.__create_bare_minimum_parser()
        self.__create_build_parser()
        self.__create_run_parser()

        # return Parsed Args
        return parser.parse_args()
