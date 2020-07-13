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

"""
Run tests for arpa
"""

import os
import logging
import sys
import math
import datetime
import pathlib
import subprocess
import shutil
import json
import uuid

cur_dir = os.path.dirname(__file__)

TESTS_DIR = "tests"
BUILDS_DIR = "builds"
ARPA_DIR = "arpa"
LOGS_DIR = "logs"

BUILD_COMMANDS_JSON = "build_commands.json"

def create_if_inexistant(direc):
    """ remove, then recreate a directory """
    if direc.exists() and direc.is_dir():
        shutil.rmtree(direc)
    direc.mkdir()

def run_test(test, build_cmd, timestamp, results):
    """ Run a single test """
    test_root_dir = pathlib.Path(TESTS_DIR) / test
    submod_root_path = (test_root_dir / test)
    logs_path = (test_root_dir / LOGS_DIR)
    logs_path.mkdir(exist_ok=True)

    # BUILD
    build_path = (test_root_dir / BUILDS_DIR)
    create_if_inexistant(build_path)

    build_cmd.extend(["-S", str(submod_root_path)])
    build_cmd.extend(["-B", str(build_path)])
    p_build = subprocess.Popen(
        build_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True)

    stdout_build, _ = p_build.communicate()
    if p_build.returncode:
        results["build_err"].append(test[0])
        return

    # ARPA BUILD JSON
    arpa_path = (test_root_dir / ARPA_DIR)
    create_if_inexistant(arpa_path)

    comp_cmds_path = (build_path / "compile_commands.json")
    arpa_out_path = (arpa_path / "int_rep.json")
    arpa_cmd = ["arpa", "build",
                   "-cc", comp_cmds_path,
                   "-r", submod_root_path,
                   "-jp", arpa_out_path
                   ]

    p_arpa = subprocess.Popen(
        arpa_cmd, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True)

    stdout_arpa, _ = p_arpa.communicate()

    log_file = (logs_path / ("%s.txt" % timestamp)).resolve()
    with open(log_file, "w") as handle:
        print(stdout_build, file=handle)
        print(stdout_arpa, file=handle)
    tmp_link = logs_path / ("latest-%s" % uuid.uuid4())
    os.symlink(log_file, tmp_link)
    os.rename(tmp_link, logs_path / "latest")

    if p_arpa.returncode:
        results["fail"].append(test)
    else:
        results["pass"].append(test)

    # TODO test arpa makefile command


def main():
    """ Run all tests """

    logging.basicConfig(
        level=logging.INFO, format="arpa-test: %(message)s")

    # TODO voluptuous

    results = {
        "pass": [],
        "fail": [],
        "build_err": []
    }

    stamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    # Build Commands JSON
    with open(BUILD_COMMANDS_JSON, "r") as json_file:
        build_cmds_json = json.load(json_file)

    n_tests = len(os.listdir(TESTS_DIR))
    width = int(math.log10(n_tests)) + 1
    cnt = 1
    for test in os.listdir(TESTS_DIR):
        print("\rrunning test {cnt:{width}}/{n_tests}".format(
            cnt=cnt, width=width, n_tests=n_tests), end="")
        sys.stdout.flush()
        cnt += 1
        build_cmd = build_cmds_json[test]
        run_test(test, build_cmd, stamp, results)

    print()
    for result, tests in results.items():
        for test in tests:
            print("%s %s" % (result.upper(), test))
    print("{n_pass:{width}}/{n_tests} tests passed".format(
        n_pass=len(results["pass"]), width=width, n_tests=n_tests))

    sys.exit(1 if results["fail"] else 0)

if __name__ == "__main__":
    main()
