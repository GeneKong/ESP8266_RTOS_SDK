#!/usr/bin/python
# Copyright 2018 Gene Kong
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# This file is use for collect compile information

import sys
import os
import os.path
import argparse
import re

from collections import OrderedDict

from progen.tools_supported import ToolsSupported
from progen.commands import argparse_filestring_type, argparse_string_type
from progen.project import Project
from progen.settings import ProjectSettings

SDK_PATH = os.environ.get("IDF_PATH")
CROSS_COMPILE = os.environ.get("CROSS_COMPILE")

if not SDK_PATH:
    print("Please set environment variable: IDF_PATH")
    exit(1)
if not CROSS_COMPILE:
    print("Please set environment variable: CROSS_COMPILE")
    exit(1)

app_gen_path = os.path.abspath(sys.argv[1])
APP_WORK_DIR = app_gen_path[:app_gen_path.rindex("build") -1]

# 0 -> scripts name
# 1 .. -> input file

"""
files_db.files :
    {
        "path": "/mnt/k/fastembedded/FASTEMBEDDED_RTOS_SDK/components/feHAL/ST/STM32F4xx_HAL_Driver/Src/stm32f4xx_hal_nor.c",
        "opath" : "",
        "component" : "",
        "macros" : ["xx", "yy=1"],
        "include" : ["include=xx.h"],
        "incdir" : ["/abc", "ecd/a/"],
        "options" : ["-Og", "-Wall"],
    }
files_db.linker :
    {
        "opath" : "",
        "options" : [],
    }
"""
OPTS_MACRO = "-D"
OPTS_INCLUDE = "-include"
OPTS_INCDIR = "-I"
OPTS_OPATH = "-o"
OPTS_LINK_FILE = "-T"
OPTS_LINK_LIBDIR = "-L"
OPTS_LINK_LIB = "-l"

options_with_arg = [OPTS_MACRO, OPTS_INCLUDE, OPTS_INCDIR, OPTS_OPATH, "-u", "-Xlinker", OPTS_LINK_FILE, OPTS_LINK_LIB, OPTS_LINK_LIBDIR]
options_exclude = ["-c", "-Wl,--start-group", "-Wl,--end-group"]

c_source_file_ext = [".c" ]
cpp_source_file_ext = [".cc", ".cpp", ".cxx"]
asm_source_file_ext  = [".S", ".s"]

def parse_compile_options(options, path, name) :
    files_obj = {
        "path": path,
        "component": name,
        "opath" : "",
        "macros": [],
        "include": [],
        "incdir" : [],
        "options" : []
    }
    i = 0
    while i < len(options):
        # process macros
        if options[i].startswith(OPTS_MACRO) :
            if len(options[i]) == len(OPTS_MACRO):
                files_obj["macros"].append(options[i + 1])
            else:
                files_obj["macros"].append(options[i][len(OPTS_MACRO):])

            if("__ESP_FILE__" in files_obj["macros"][-1]):
                files_obj["macros"].pop(-1)

        elif options[i].startswith(OPTS_INCLUDE) :
            if len(options[i]) == len(OPTS_INCLUDE):
                files_obj["include"].append(options[i + 1])
            else:
                files_obj["include"].append(options[i][len(OPTS_INCLUDE):])
        elif options[i].startswith(OPTS_INCDIR) :
            if len(options[i]) == len(OPTS_INCDIR):
                files_obj["incdir"].append(options[i + 1])
            else:
                files_obj["incdir"].append(options[i][len(OPTS_INCDIR):])
        elif options[i].startswith(OPTS_OPATH) :
            if len(options[i]) == len(OPTS_OPATH):
                files_obj["opath"] = options[i + 1]
            else:
                files_obj["opath"] = options[i][len(OPTS_OPATH):]
        elif options[i] in options_exclude:
            pass
        else:
            if options[i] in options_with_arg:
                files_obj["options"].append(options[i] + " " + options[i + 1])
            else:
                files_obj["options"].append(options[i])

        if options[i] in options_with_arg:
            i += 2
        else:
            i += 1
    return files_obj

def parse_linker_options(options) :
    linker_obj = {"opath" : "", "options":[], "lib": [], "ld": [], "L":[]}
    i = 0
    while i < len(options):
        # process
        if not options[i].endswith(".o") :
            if options[i].startswith(OPTS_OPATH) :
                if len(options[i]) == len(OPTS_OPATH):
                    linker_obj["opath"] = options[i + 1]
                    i += 1
                else:
                    linker_obj["opath"] = options[i][len(OPTS_OPATH):]
            elif options[i].startswith(OPTS_LINK_FILE) :
                if len(options[i]) == len(OPTS_LINK_FILE):
                    linker_obj["ld"].append(options[i + 1])
                else:
                    linker_obj["ld"].append(options[i][len(OPTS_LINK_FILE):])
            elif options[i].startswith(OPTS_LINK_LIBDIR) :
                if len(options[i]) == len(OPTS_LINK_LIBDIR):
                    linker_obj["L"].append(options[i + 1])
                else:
                    linker_obj["L"].append(options[i][len(OPTS_LINK_LIBDIR):])
            elif options[i].startswith(OPTS_LINK_LIB) :
                if len(options[i]) == len(OPTS_LINK_LIB):
                    linker_obj["lib"].append(options[i + 1])
                else:
                    linker_obj["lib"].append(options[i][len(OPTS_LINK_LIB):])            
            elif options[i] in options_exclude:
                pass
            else:
                if options[i] in options_with_arg:
                    linker_obj["options"].append(options[i] + " " + options[i + 1])
                else:
                    linker_obj["options"].append(options[i])
        if options[i] in options_with_arg:
            i += 2
        else:
            i += 1
    return linker_obj

class DataObj(object):
    def __init__(self):
        self.comm = { "flags": set([]), "macros": set([]) }
        self.c = { "flags": set([]), "macros": set(["__ESP_FILE__=__FILE__"]) }
        self.cpp = { "flags": set([]), "macros": set(["__ESP_FILE__=__FILE__"]) }
        self.asm = { "flags": set([]), "macros": set(["__ESP_FILE__=__FILE__"]) }
        self.linker = { "flags": set([]), "search_paths": set([]), "script_files": set([]) }
        self.incdirs = OrderedDict()
        self.includes = []
        self.sources = {}

    def feedFileOptions(self, obj):
        file_ext = "." + obj["path"].split(".")[-1].lower()
        if file_ext in c_source_file_ext:
            self.c["flags"] = self.c["flags"] | set(obj["options"])
            self.c["macros"] = self.c["macros"] | set(obj["macros"])
        elif file_ext in cpp_source_file_ext:
            self.cpp["flags"] = self.cpp["flags"] | set(obj["options"])
            self.cpp["macros"] = self.cpp["macros"] | set(obj["macros"])
        elif file_ext in asm_source_file_ext:
            self.asm["flags"] = self.asm["flags"] | set(obj["options"])
            self.asm["macros"] = self.asm["macros"] | set(obj["macros"])

        self.comm["flags"] = self.comm["flags"]
        for include in obj["include"]:
            if include not in self.includes:
                self.includes.append(include)

        for include in obj["incdir"]:
            if include.startswith(SDK_PATH):
                group_name = include[len(SDK_PATH) + 1:]
            elif include.startswith(APP_WORK_DIR):
                group_name = include[len(APP_WORK_DIR) + 1:]                
            else :
                print("Warn can't found relative include path(%s) in %s."%(include, [SDK_PATH, APP_WORK_DIR]))
                continue
            self.incdirs[group_name] = os.path.relpath(include, APP_WORK_DIR+ "/dummy")

        group_name = os.path.dirname(obj["path"])
        if group_name.startswith(SDK_PATH):
            group_name = group_name[len(SDK_PATH) + 1:]

        elif group_name.startswith(APP_WORK_DIR):
            group_name = group_name[len(APP_WORK_DIR) + 1:]
        else:
            print("Error found relative sources path in %s.", str(obj))
            exit(3)

        self.sources.setdefault(group_name, []).append(os.path.relpath(obj["path"], APP_WORK_DIR + "/dummy"))

    def feedLinkerOptions(self, obj):
        self.linker["flags"] = set(obj["options"])
        self.linker["search_paths"] = set(obj["L"])
        self.linker["script_files"] = set(obj["ld"])
        self.linker["libraries"] = set(obj["lib"])

    def genDicts(self, name):
        project_dicts = {"name": name}
        project_dicts["common"] = {
            "flags": None,
            "macros": None,
        }
        project_dicts["c"] = {
            "flags": None,
            "macros": None,
        }
        project_dicts["cxx"] = {
            "flags": None,
            "macros": None,
        }
        project_dicts["asm"] = {
            "flags": None,
            "macros": None,
        }
        project_dicts["linker"] = {
            'flags':None,
            'script_files': None,
            'search_paths': None,
            'libraries': None
        }
        comm_macros = self.c["macros"] & self.cpp["macros"] & self.asm["macros"]
        comm_flags = (self.c["flags"] & self.cpp["flags"] & self.asm["flags"] & self.linker["flags"]) | self.comm["flags"]

        file_macros = []
        for inc in self.incdirs.keys():
            for f in self.includes:
                # check file if "build/include" + f exists?
                if os.path.exists(inc + "/" + f) :
                    with open(inc + "/" + f) as f:
                        ctx = f.read()
                        for macro in re.findall("#define\s+(\w+)\s+(.*?)\n", ctx):
                            file_macros.append("%s=%s" % macro)

        project_dicts["common"]["macros"] = list(comm_macros | set(file_macros))
        project_dicts["common"]["flags"] = list(comm_flags)
        project_dicts["c"]["macros"] = list(self.c["macros"] - comm_macros)
        project_dicts["c"]["flags"] = list(self.c["flags"] - comm_flags)
        project_dicts["cxx"]["macros"] = list(self.cpp["macros"] - comm_macros)
        project_dicts["cxx"]["flags"] = list(self.cpp["flags"] - comm_flags)
        project_dicts["asm"]["macros"] = list(self.asm["macros"] - comm_macros)
        project_dicts["asm"]["flags"] = list(self.asm["flags"] - comm_flags)

        project_dicts["linker"]["flags"] = list(self.linker["flags"] - comm_flags)
        project_dicts["linker"]["script_files"] = list(self.linker["script_files"])
        project_dicts["linker"]["libraries"] = list(self.linker["libraries"])
        project_dicts["linker"]["search_paths"] = list(self.linker["search_paths"])

        project_dicts["subsrc"] = {}
        project_dicts["files"] = {"includes": self.incdirs, "sources": self.sources}

        return project_dicts

class Generator:
    def __init__(self, obj) :
        self.settings = ProjectSettings()
        self.settings.properties = []
        self.basepath = "."
        self.projects_dict = {
            "toolchains":{"gcc":"", "gcc_prefix":CROSS_COMPILE}
        }
        self.pobj = obj
    
    def generate(self, name='', tool='gnu_mcu_eclipse'):
        self.project = Project(name, tool, None, self.settings, self, None, self.pobj.genDicts(name))
        return self.project.generate()

    def push_properties(self):
        pass

    def pop_properties(self):
        pass

    def merge_properties_without_override(self, prop_dict):
        pass


if __name__ == '__main__':
    # Parse Options
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-t", "--tool", help="Create project files for provided tool", default='gnu_mcu_eclipse',
        type=argparse_string_type(str.lower, False), choices=list(ToolsSupported.TOOLS_DICT.keys()) + list(ToolsSupported.TOOLS_ALIAS.keys()))
    parser.add_argument(
        "-p", "--project", help="Project to be generated", default = 'App')
    parser.add_argument('file')
    args = parser.parse_args()

    data_obj = DataObj()
    with open(args.file, "r") as f:        
        for line in f:
            items = line.split()
            if items[-1].endswith(".map") :    
                data_obj.feedLinkerOptions(parse_linker_options(items[:-1]))
            else:
                data_obj.feedFileOptions(parse_compile_options(items[1:-1], items[-1], items[0]))
    
    generate = Generator(data_obj)
    generate.generate(args.project, args.tool)