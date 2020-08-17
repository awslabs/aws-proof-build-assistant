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
This module contains classes and functions related to building a file-specific Makefile
'''


import os
import logging
import sys
import lib.arpa_helper as helper

# @dataclasses
class MakefileData():
    ''' DataClass that contains information found within a Makefile '''
    includes = []
    defines = []
    proof_sources = []
    project_sources = []
    other_dependencies = []
    missing_dependencies = {}


class MakefileReadyContents:
    ''' class that contains all the info needed to create a makefile for a given harness '''

    def __init__(self, info):
        self.raw_info = info
        self.variable_2_path = {}

        self.data = MakefileData()

    def __shortcut_path(self, paths, prefix):
        #TODO this is very complicated
        ''' replace project root and proofs root path with Makefile variable '''
        new_paths = {"proof":[],
                     "project":[],
                     "none":[]}
        for path in paths:
            key, new_path = self.__check_com_prefixes(path)
            new_paths[key].append("%s%s" % (prefix, new_path))

        for key in new_paths:
            new_paths[key] = sorted(new_paths[key])
        return new_paths

    def __check_com_prefixes(self, path):
        #TODO this is very complicated
        ''' check if prefix is a prefix of path. return updated path '''
        for cat in self.variable_2_path:
            for prefix_path in self.variable_2_path[cat]:
                if os.path.commonprefix([path, prefix_path]) == prefix_path:
                    if path == prefix_path:
                        return (cat, self.__make_val(self.variable_2_path[cat][prefix_path]))

                    rel_path = os.path.relpath(path, prefix_path)
                    return (cat, os.path.join(
                        self.__make_val(self.variable_2_path[cat][prefix_path]), rel_path))

        return ("none", path)

    def __make_val(self, var):
        ''' return MAKE syntax for accessing a variable value '''
        return "$(" + str(var) + ")"

    def __add_prefix(self, items, prefix):
        ''' add prefix flag to input items. Return list '''
        new_items = ["%s%s" % (prefix, i) for i in items]
        return sorted(new_items)

    def process_custom_info(self):
        ''' add Makefile shortcuts to paths in MakefileInfo '''
        includes_2_shortcut_path = \
            self.__shortcut_path(self.raw_info.includes, helper.CC_INCLUDE)
        _ = [self.data.includes.extend(includes_2_shortcut_path[k])
             for k in includes_2_shortcut_path]

        self.data.defines = self.__add_prefix(self.raw_info.defines, helper.CC_DEFINE)

        dependencies_2_shortcut_path = self.__shortcut_path(self.raw_info.dependencies, "")
        self.data.proof_sources = dependencies_2_shortcut_path["proof"]
        self.data.project_sources = dependencies_2_shortcut_path["project"]
        self.data.other_dependencies = dependencies_2_shortcut_path["none"]
        self.data.missing_dependencies = self.raw_info.missing_dependencies # unordered

    def set_variable_2_path(self, args):
        ''' create a map between dependency types and (variable, path) pairs '''
        self.variable_2_path = {"proof" : {
            # args.make_proofs_path: args.make_proofs_name,
            args.make_proof_source_path: args.make_proof_source_variable,
            args.make_proof_stub_path: args.make_proof_stub_variable},
                                "project" : {
                                    args.make_root_path: args.make_root_variable}}


class Makefile:
    ''' Class that stores Makefile-related info and that can generate a makefile '''

    def __init__(self, args):
        self.contents_raw = helper.FileSpecificInfo()
        self.contents_processed = MakefileReadyContents(self.contents_raw)

        self.args = args
        self.save_path = ""
        self.directory = ProofDirectory()
        self.textual_representation = []

    def set_save_path(self, path):
        ''' set the save_path field '''
        self.save_path = path

    def __add_initial_comment_to_text(self):
        self.textual_representation.append("# This file is generated automatically by \
            {}".format(helper.TOOL_NAME))
        self.textual_representation.append("")

    def __add_directory_paths_to_text(self):
        # currently not called
        self.textual_representation.append("%s = %s" % (self.args.make_root_variable,
                                                        self.args.make_root_path))
        self.textual_representation.append("%s = %s" % (self.args.make_proof_source_variable,
                                                        self.args.make_proof_source_path))
        # self.textual_representation.append("%s = %s" % (self.args.make_proofs_name,
        #                                                 self.args.make_proofs_path))
        self.textual_representation.append("")

    def __add_entry_info_to_text(self):
        # currently not called
        entry_name, _ = os.path.splitext(os.path.basename(self.directory.harness_path))
        if not entry_name.endswith("_harness"):
            logging.error("invalid harness name: %s", self.directory.harness_path)
            sys.exit(1)
        function_name = entry_name[:-len("_harness")]
        if self.args.shorten_entry:
            entry_name = function_name
        self.textual_representation.append("%s = %s" % (self.args.entry_name, entry_name))
        self.textual_representation.append("%s = %s.c" % (self.args.entry_file,
                                                          "$(" + str(self.args.entry_name) + ")"))
        self.textual_representation.append("")

    def __add_custom_info_to_text(self):
        lines_to_add = []
        lines_to_add.extend(self.__append_variable(self.contents_processed.data.defines,
                                                   self.args.define_variable))
        lines_to_add.extend(self.__append_variable(self.contents_processed.data.includes,
                                                   self.args.include_variable))
        lines_to_add.extend(self.__append_variable(self.contents_processed.data.proof_sources,
                                                   self.args.make_proof_sources_variable))
        lines_to_add.extend(self.__append_variable(self.contents_processed.data.project_sources,
                                                   self.args.make_project_sources_variable))
        lines_to_add.extend(self.__append_variable(self.contents_processed.data.other_dependencies,
                                                   "# EXTERNAL_DEPENDENCIES"))

        self.textual_representation.extend(lines_to_add)

    def __append_variable(self, elements, label):
        ''' return a list of Makefile commands associated to a specific variable '''
        lines = ["%s += %s" % (label, e) for e in elements]
        lines.append("")
        return lines

    def __add_missing_to_makefile(self):
        ''' return a list of comments for the missing dependencies'''
        lines_to_add = []
        lines_to_add.append("")
        lines_to_add.append("# The proof also calls into the following functions, whose source")
        lines_to_add.append("# files could not be determined.")
        lines_to_add.append("# You may need to find the files these functions reside in")
        lines_to_add.append("# and add them to the $(PROJECT_SOURCES) array.")

        for source, functions in self.contents_processed.data.missing_dependencies.items():
            file = source[0]
            func = source[1]
            lines_to_add.extend(["# * <%s>   in %s:%s" % (f, file, func) for f in functions])

        self.textual_representation.extend(lines_to_add)

    def build(self, internal_rep):
        ''' create an internal textual representation of a Makefile to generate '''
        harness_path = self.directory.harness_path
        if harness_path not in internal_rep[helper.JSON_FILE]:
            logging.error("<%s> not found in given internal representation. "
                          "Try rebuilding the internal rep.", harness_path)
            sys.exit(1)

        self.__add_initial_comment_to_text()
        # self.__add_directory_paths_to_text()
        # self.__add_entry_info_to_text()

        harness_functions = \
            internal_rep[helper.JSON_FILE][harness_path][helper.JSON_FCT].keys()
        self.contents_raw.find_custom_info_recursively(self.args.change_dependency_extensions,
                                                       internal_rep, harness_path,
                                                       harness_functions)

        # find and process custom build info
        self.contents_processed.set_variable_2_path(self.args)
        self.contents_processed.process_custom_info()

        self.__add_custom_info_to_text()
        self.__add_missing_to_makefile()


    def save(self):
        ''' generate a Makefile based on instance contents '''
        with open(self.save_path, "w") as output:
            print("\n".join(self.textual_representation), file=output)
        print("-- Created {} Makefile at \
            {}".format(helper.TOOL_NAME, os.path.abspath(self.save_path)))


class ProofDirectory:
    ''' Class that encapsulates the contents of a Proof directory '''

    def __init__(self):
        self.path = ""
        self.harness_path = ""

    def set_harness_path(self, input_path):
        ''' find harness file in current directory. Return its path '''
        harness_path = ""
        # if harness path is given
        if input_path:
            harness_path = os.path.abspath(input_path)
            if not os.path.exists(harness_path):
                logging.error("Specified path does not point to an existing file: %s", harness_path)
                sys.exit(1)
            self.harness_path = harness_path
            self.path = os.path.abspath(os.path.dirname(harness_path))
            return

        # look for harness in cwd
        found_harness = False
        for file in os.listdir("."):
            if file.endswith("_harness.c"):
                if found_harness:
                    logging.error("too many harness files in current directory!!")
                    sys.exit(1)
                harness_path = os.path.abspath(file)
                found_harness = True

        if not found_harness:
            logging.error("no harness found in current directory!!")
            sys.exit(1)
        self.harness_path = harness_path
        self.path = os.path.abspath(os.path.dirname(harness_path))
