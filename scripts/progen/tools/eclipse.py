# Copyright 2014-2015 0xc0170
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

import copy
import logging

from collections import OrderedDict
# eclipse works with linux paths
from os.path import normpath, join, basename, exists

from .tool import Tool, Builder, Exporter
from .gcc import MakefileGcc
from ..util import SOURCE_KEYS, fix_special_symbol, fixed_path_2_unix_style

logger = logging.getLogger('progen.tools.eclipse_make_gcc')

class EclipseMakeGcc(Tool, Exporter, Builder):

    file_types = {'cpp': 1, 'c': 1, 's': 1, 'obj': 1, 'lib': 1, 'h': 1}

    generated_project = {
        'path': '',
        'files': {
            'proj_file': '',
            'cproj': '',
            'makefile': '',
        }
    }

    def __init__(self, workspace, env_settings):
        self.definitions = 0
        self.exporter = MakefileGcc(workspace, env_settings)
        self.workspace = workspace
        self.env_settings = env_settings

    @staticmethod
    def get_toolnames():
        return ['eclipse_make_gcc']

    @staticmethod
    def get_toolchain():
        return 'gcc'

    def _expand_one_file(self, source, new_data, extension):
        # use reference count to instead '..'
        source = normpath(source).replace('..\\', '')
        return {"path": join('PARENT-%d-PROJECT_LOC' % source.count("../"), source).replace('../', '').replace('\\', '/'),
                "name": basename(source), 
                "type": self.file_types[extension.lower()]}

    def _expand_sort_key(self, file) :
        return file['name'].lower()

    def export_workspace(self):
        logger.debug("Current version of CoIDE does not support workspaces")

    def export_project(self):
        """ Processes groups and misc options specific for eclipse, and run generator """

        output = copy.deepcopy(self.generated_project)
        expanded_dic = self.workspace.copy()
        expanded_dic["toolchains"] = copy.copy(self.workspace["toolchains"])
        expanded_dic["misc"] = self._fix_cmd_path(copy.copy(self.workspace["misc"]))
        expanded_dic["macros"] = self._fix_macro_quot(expanded_dic["macros"])        
        
        # process path format in windows
        for name in ['include_paths', 'source_paths','include_paths', 'linker_search_paths', 'lib_search_paths',
                     'source_files_c', 'source_files_cpp', 'source_files_s']:            
            expanded_dic[name] = fixed_path_2_unix_style(expanded_dic[name])
            
        expanded_dic['linker']['search_paths'] = fixed_path_2_unix_style(expanded_dic['linker']['search_paths'])
                        
        groups = self._get_groups(expanded_dic)
        expanded_dic['groups'] = {}
        for group in groups:
            expanded_dic['groups'][group] = []
        self._iterate(self.workspace, expanded_dic)

        expanded_dic['src_groups'] = []
        for group in self._get_src_groups(expanded_dic):
            rgrp = group.split("/")[0]
            if rgrp not in expanded_dic['src_groups']:
                expanded_dic['src_groups'].append(rgrp)

        c_flags = []
        cxx_flags = []
        asm_flags = []
        ld_flags = []

        if expanded_dic["toolchains"]["gcc_prefix"].startswith("arm"):
            self.update_arm_options(expanded_dic, c_flags, cxx_flags, asm_flags, ld_flags)
        elif expanded_dic["toolchains"]["gcc_prefix"].startswith("riscv"):
            self.update_riscv_options(expanded_dic, c_flags, cxx_flags, asm_flags, ld_flags)
        else:
            self.update_cross_options(expanded_dic, c_flags, cxx_flags, asm_flags, ld_flags)

        expanded_dic["options"]["other_ld_flags"] = " ".join(ld_flags)
        expanded_dic["options"]["other_c_flags"]  = " ".join(c_flags)
        expanded_dic["options"]["other_cxx_flags"] = " ".join(cxx_flags)
        expanded_dic["options"]["other_asm_flags"] = " ".join(asm_flags)
        
        # just fixed for gnu mcu eclipse project
        expanded_dic["include_paths"] = self._fix_gnu_mcu_path(expanded_dic["include_paths"])
        expanded_dic["linker_search_paths"] = self._fix_gnu_mcu_path(expanded_dic["linker_search_paths"])

        project_path, output['files']['cproj'] = self.gen_file_jinja(
            'eclipse_makefile.cproject.tmpl', expanded_dic, '.cproject', expanded_dic['output_dir']['path'])

        project_path, output['files']['proj_file'] = self.gen_file_jinja(
            'eclipse.project.tmpl', expanded_dic, '.project', expanded_dic['output_dir']['path'])
        return output
    
    def _fix_gnu_mcu_path(self, paths):
        npaths = []
        for path in paths:
            if not exists(path):
                npaths.append("../" + path)
            else:
                npaths.append(path)
        return npaths
    
    def _fix_cmd_path(self, misc):
        _misc = copy.copy(misc)
        if not _misc: return _misc
        for cmd in ["pre_cmd", "post_cmd"]:
            if cmd in misc:
                _misc[cmd] = []
                for line in misc[cmd]:                    
                    _misc[cmd].append(fix_special_symbol(line))
            _misc[cmd] = ";".join(_misc[cmd])
        return _misc
    
    def _fix_macro_quot(self, macros):
        _macros = {}
        for key,values in list(macros.items()):
            _macros[key] = []
            for macro in values:
                #_macros[key].append("'" + fix_special_symbol(macro) + "'")
                _macros[key].append(fix_special_symbol(macro))
        return _macros

    def get_generated_project_files(self):
        return {'path': self.workspace['path'], 'files': [self.workspace['files']['proj_file'], self.workspace['files']['cproj'],
            self.workspace['files']['makefile']]}

    def update_cross_options(self, expanded_dic, c_flags, cxx_flags, asm_flags, ld_flags):
        expanded_dic["options"] = {}
        for name in ["common", "ld", "c", "cxx", "asm"] :
            for flag in expanded_dic['flags'][name] :
                if flag.startswith("-ggdb") :
                    pass
                elif name == "common" :
                    c_flags.append(flag)
                    cxx_flags.append(flag)
                    asm_flags.append(flag)
                elif name == "c" :
                    c_flags.append(flag)
                elif name == "cxx" :
                    cxx_flags.append(flag)
                elif name == "asm" :
                    asm_flags.append(flag)
                else:
                    ld_flags.append(flag)