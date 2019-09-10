# Copyright 2017-2020
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
import os

# eclipse works with linux paths
from os.path import normpath, join, basename, exists

from .tool import Tool, Builder, Exporter
from .gcc import MakefileGcc
from ..util import fix_special_symbol, fixed_path_2_unix_style

logger = logging.getLogger('progen.tools.st_cube_eclipse')
    
class EclipseStCube(Tool, Exporter, Builder):

    file_types = {'cc': 1, 'cxx': 1, 'cpp': 1, 'c': 1, 's': 1, 'obj': 1, 'lib': 1, 'h': 1, 'hh' : 1}

    generated_project = {
        'path': '',
        'files': {
            'proj_file': '',
            'cproj': ''
        }
    }
    
    #GNU MCU Plugin ID
    MFPU_COMMAND2ID = {
        "default":"default",
        "-mfpu=crypto-neon-fp-armv8":"crypto-neon-fp-armv8",
        "-mfpu=fpa":"fpa",
        "-mfpu=fpe2":"fpe2",
        "-mfpu=fpe3":"fpe3",
        "-mfpu=fp-armv8":"fparmv8",
        "-mfpu=fpv4-sp-d16":"fpv4-sp-d16",
        "-mfpu=fpv5-d16":"fpv5-d16",
        "-mfpu=fpv5-sp-d16":"fpv5-sp-d16",
        "-mfpu=maverick":"maverick",
        "-mfpu=neon":"neon",
        "-mfpu=neon-fp16":"neon-fp16",
        "-mfpu=neon-fp-armv8":"neon-fp-armv8",
        "-mfpu=neon-vfpv4":"neon-vfpv4",
        "-mfpu=vfp":"vfp",
        "-mfpu=vfpv3":"vfpv3",
        "-mfpu=vfpv3-d16":"vfpv3-d16",
        "-mfpu=vfpv3-d16-fp16":"vfpv3-d16-fp16",
        "-mfpu=vfpv3-fp16":"vfpv3-fp16",
        "-mfpu=vfpv3xd":"vfpv3xd",
        "-mfpu=vfpv3xd-fp16":"vfpv3xd-fp16",
        "-mfpu=vfpv4":"vfpv4",
        "-mfpu=vfpv4-d16":"vfpv4-d16"
    }
    
    @staticmethod
    def get_mfpu_gnuarmeclipse_id(command):
        trip_cmd = command.strip().lower()
        if trip_cmd not in EclipseStCube.MFPU_COMMAND2ID:
            trip_cmd = "default"
        return EclipseStCube.MFPU_COMMAND2ID[trip_cmd]
    
    FPUABI_COMMAND2ID = { 
        "":"default",
        "-mfloat-abi=soft":"soft",
        "-mfloat-abi=softfp":"softfp",
        "-mfloat-abi=hard":"hard"
    }
    
    @staticmethod
    def get_fpuabi_gnuarmeclipse_id(command):
        trip_cmd = command.strip().lower()
        if trip_cmd not in EclipseStCube.FPUABI_COMMAND2ID:
            trip_cmd = ""
        return EclipseStCube.FPUABI_COMMAND2ID[trip_cmd]
    
    MCPU_COMMAND2ID = {
        "-mcpu=arm1020e":"arm1020e",
        "-mcpu=arm1020t":"arm1020t",
        "-mcpu=arm1022e":"arm1022e",
        "-mcpu=arm1026ej-s":"arm1026ej-s",
        "-mcpu=arm10e":"arm10e",
        "-mcpu=arm10tdmi":"arm10tdmi",
        "-mcpu=arm1136j-s":"arm1136j-s",
        "-mcpu=arm1136jf-s":"arm1136jf-s",
        "-mcpu=arm1156t2-s":"arm1156t2-s",
        "-mcpu=arm1156t2f-s":"arm1156t2f-s",
        "-mcpu=arm1176jz-s":"arm1176jz-s",
        "-mcpu=arm1176jzf-s":"arm1176jzf-s",
        "-mcpu=arm2":"arm2",
        "-mcpu=arm250":"arm250",
        "-mcpu=arm3":"arm3",
        "-mcpu=arm6":"arm6",
        "-mcpu=arm60":"arm60",
        "-mcpu=arm600":"arm600",
        "-mcpu=arm610":"arm610",
        "-mcpu=arm620":"arm620",
        "-mcpu=arm7":"arm7",
        "-mcpu=arm70":"arm70",
        "-mcpu=arm700":"arm700",
        "-mcpu=arm700i":"arm700i",
        "-mcpu=arm710":"arm710",
        "-mcpu=arm7100":"arm7100",
        "-mcpu=arm710c":"arm710c",
        "-mcpu=arm710t":"arm710t",
        "-mcpu=arm720":"arm720",
        "-mcpu=arm720t":"arm720t",
        "-mcpu=arm740t":"arm740t",
        "-mcpu=arm7500":"arm7500",
        "-mcpu=arm7500fe":"arm7500fe",
        "-mcpu=arm7d":"arm7d",
        "-mcpu=arm7di":"arm7di",
        "-mcpu=arm7dm":"arm7dm",
        "-mcpu=arm7dmi":"arm7dmi",
        "-mcpu=arm7m":"arm7m",
        "-mcpu=arm7tdmi":"arm7tdmi",
        "-mcpu=arm7tdmi-s":"arm7tdmi-s",
        "-mcpu=arm8":"arm8",
        "-mcpu=arm810":"arm810",
        "-mcpu=arm9":"arm9",
        "-mcpu=arm920":"arm920",
        "-mcpu=arm920t":"arm920t",
        "-mcpu=arm922t":"arm922t",
        "-mcpu=arm926ej-s":"arm926ej-s",
        "-mcpu=arm940t":"arm940t",
        "-mcpu=arm946e-s":"arm946e-s",
        "-mcpu=arm966e-s":"arm966e-s",
        "-mcpu=arm968e-s":"arm968e-s",
        "-mcpu=arm9e":"arm9e",
        "-mcpu=arm9tdmi":"arm9tdmi",
        "-mcpu=cortex-a12":"cortex-a12",
        "-mcpu=cortex-a15":"cortex-a15",
        "-mcpu=cortex-a17":"cortex-a17",
        "-mcpu=cortex-a32":"cortex-a32",
        "-mcpu=cortex-a35":"cortex-a35",
        "-mcpu=cortex-a5":"cortex-a5",
        "-mcpu=cortex-a53":"cortex-a53",
        "-mcpu=cortex-a57":"cortex-a57",
        "-mcpu=cortex-a7":"cortex-a7",
        "-mcpu=cortex-a72":"cortex-a72",
        "-mcpu=cortex-a8":"cortex-a8",
        "-mcpu=cortex-a9":"cortex-a9",
        "-mcpu=cortex-m0":"cortex-m0",
        "-mcpu=cortex-m0.small-multiply":"cortex-m0-small-multiply",
        "-mcpu=cortex-m0plus":"cortex-m0plus",
        "-mcpu=cortex-m0plus.small-multiply":"cortex-m0plus-small-multiply",
        "-mcpu=cortex-m1":"cortex-m1",
        "-mcpu=cortex-m1.small-multiply":"cortex-m1-small-multiply",
        "-mcpu=cortex-m23":"cortex-m23",
        # default          
        "-mcpu=cortex-m3":"cortex-m3",
        "-mcpu=cortex-m33":"cortex-m33",
        "-mcpu=cortex-m4":"cortex-m4",
        "-mcpu=cortex-m7":"cortex-m7",
        "-mcpu=cortex-r4":"cortex-r4",
        "-mcpu=cortex-r4f":"cortex-r4f",
        "-mcpu=cortex-r5":"cortex-r5",
        "-mcpu=cortex-r7":"cortex-r7",
        "-mcpu=cortex-r8":"cortex-r8",
        "-mcpu=ep9312":"ep9312",
        "-mcpu=exynos-m1":"exynos-m1",
        "-mcpu=fa526":"fa526",
        "-mcpu=fa606te":"fa606te",
        "-mcpu=fa626":"fa626",
        "-mcpu=fa626te":"fa626te",
        "-mcpu=fa726te":"fa726te",
        "-mcpu=fmp626":"fmp626",
        "-mcpu=generic-armv7-a":"generic-armv7-a",
        "-mcpu=iwmmxt":"iwmmxt",
        "-mcpu=iwmmxt2":"iwmmxt2"
    }
    
    @staticmethod
    def get_mcpu_gnuarmeclipse_id(command):
        trip_cmd = command.strip().lower()
        if trip_cmd not in EclipseStCube.MCPU_COMMAND2ID:
            trip_cmd = "-mcpu=cortex-m3"
        return EclipseStCube.MCPU_COMMAND2ID[trip_cmd]
    
    OPTIMIZATIONLEVEL_COMMAND2ID = { 
        "-O0":"none",
        "-O1":"optimize",
        "-O2":"more",
        "-O3":"most",
        "-Os":"size",
        "-Og":"debug",
    }
    
    @staticmethod
    def get_optimization_gnuarmeclipse_id(command):
        trip_cmd = command.strip()
        if trip_cmd not in EclipseStCube.OPTIMIZATIONLEVEL_COMMAND2ID:
            trip_cmd = "-O2"
        return EclipseStCube.OPTIMIZATIONLEVEL_COMMAND2ID[trip_cmd]
    
    DEBUGLEVEL_COMMAND2ID = { 
        "default":"g",
        "-g1":"g1",
        "-g":"g",
        "-g3":"g3"
    }
    
    @staticmethod
    def get_debug_gnuarmeclipse_id(command):
        trip_cmd = command.strip().lower()
        if trip_cmd not in EclipseStCube.DEBUGLEVEL_COMMAND2ID:
            trip_cmd = "default"
        return EclipseStCube.DEBUGLEVEL_COMMAND2ID[trip_cmd]
    
    INSTRUCTIONSET_COMMAND2ID = { 
        "":"default",
        "-mthumb":"thumb",
        "-marm":"arm"
    }
    
    @staticmethod
    def get_instructionset_gnuarmeclipse_id(command):
        trip_cmd = command.strip().lower()
        if trip_cmd not in EclipseStCube.INSTRUCTIONSET_COMMAND2ID:
            trip_cmd = ""
        return EclipseStCube.INSTRUCTIONSET_COMMAND2ID[trip_cmd]
    
    UNALIGNEDACCESS_COMMAND2ID = { 
        "":"default",
        "-munaligned-access":"enabled",
        "-mno-unaligned-access":"disabled"
    }
    
    @staticmethod
    def get_unalignedaccess_gnuarmeclipse_id(command):
        trip_cmd = command.strip().lower()
        if trip_cmd not in EclipseStCube.UNALIGNEDACCESS_COMMAND2ID:
            trip_cmd = ""
        return EclipseStCube.UNALIGNEDACCESS_COMMAND2ID[trip_cmd]
        
    #Other debug flags, Other Warning flag, Other Optimization flag
            
    def __init__(self, workspace, env_settings):
        self.definitions = 0
        self.exporter = MakefileGcc(workspace, env_settings)
        self.workspace = workspace
        self.env_settings = env_settings
            # all bool gnu mcu eclipse options store here
        self.GNU_MCU_ARM_BOOL_COMMAND2OPTIONS = {
        "-Wall":"false",
        "-Wextra":"false",
        "-fsyntax-only":"false",
        "-pedantic":"false",
        "-pedantic-errors":"false",
        "-w":"false",
        "-Wunused":"false",
        "-Wuninitialised":"false",
        "-Wmissing-declaration":"false",
        "-Wconversion":"false",
        "-Wpointer-arith":"false",
        "-Wshadow":"false",
        "-Wpadded":"false",
        "-Werror":"false",
        
        "-p":"false",
        "-pg":"false",
        
        #C
        "-fmessage-length=0":"false",
        "-fsigned-char":"false",
        "-ffunction-sections":"false",
        "-fdata-sections":"false",
        "-fno-common":"false",
        "-ffreestanding":"false",
        "-fno-move-loop-invariants":"false",
        "-Wlogical-op":"false",
        "-Waggregate-return":"false",
        "-Wfloat-equal":"false",
        '-fno-inline-functions':"false",
        '-fno-builtin':"false",
        '-fsingle-precision-constant':"false",
        '-fPIC':"false",
        '-flto':"false",
        
        #CXX
        "-nostdinc": "fasle",
        "-nostdinc++": "fasle",
        "-Wabi":"false",
        "-fno-exceptions":"false",
        "-fno-rtti":"false",
        "-fno-use-cxa-atexit":"false",
        "-fno-threadsafe-statics":"false",
        "-Wctor-dtor-privacy":"fasle",
        "-Wnoexcept":"false",
        "-Wnon-virtual-dtor":"false",
        "-Wstrict-null-sentinel":"false",
        "-Wsign-promo":"false",
        "-Weffc++":"false",
        
        #Linker
        "-Xlinker--gc-sections":"false",
        "-nostartfiles":"false",
        "-nodefaultlibs":"false",
        "-nostdlib":"false",
        "-Xlinker--print-gc-sections":"false",
        "-s":"false",
        "-Xlinker--cref":"false",
        "-Xlinker--print-map":"false",
        "--specs=nosys.specs":"false",
        "--specs=nano.specs":"false",
        "-u_printf_float":"false",
        "-u_scanf_float":"false",
        "-v":"false",
        }
    
        self.GNU_MCU_ARM_STR_COMMAND2OPTIONS = {
        
        }
    
    @staticmethod
    def get_toolnames():
        return ['st_cube_eclipse']

    @staticmethod
    def get_toolchain():
        return 'gcc'

    def _expand_one_file(self, source, new_data, extension):
        # use reference count to instead '..'
        source = normpath(source).replace('\\', '/')
        # new_data['output_dir']['rel_count']
        return {"path": join('PARENT-%d-PROJECT_LOC' % source.count("../"), source).replace('../', '').replace('\\', '/'),
                "name": basename(source), 
                "type": self.file_types[extension.lower()]}

    def _expand_sort_key(self, file) :
        return file['name'].lower()

    def update_cross_options(self, expanded_dic, c_flags, cxx_flags, asm_flags, ld_flags):
        expanded_dic["options"] = {}
        print(expanded_dic['flags'])
        for name in ["common", "ld", "c", "cxx", "asm"] :
            for flag in expanded_dic['flags'][name] :
                if flag.startswith("-O") :
                    expanded_dic["options"]["optimization"] = EclipseStCube.get_optimization_gnuarmeclipse_id(flag)
                elif flag.startswith("-ggdb") :
                    pass
                elif flag.startswith("-g") :
                    expanded_dic["options"]["debug"] = EclipseStCube.get_debug_gnuarmeclipse_id(flag)
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

    def update_arm_options(self, expanded_dic, c_flags, cxx_flags, asm_flags, ld_flags):
        expanded_dic["options"] = {}
        expanded_dic["options"]["optimization"] = EclipseStCube.get_optimization_gnuarmeclipse_id("")
        expanded_dic["options"]["debug"] = EclipseStCube.get_debug_gnuarmeclipse_id("")
        expanded_dic["options"]["mcu"] = EclipseStCube.get_mcpu_gnuarmeclipse_id("")
        expanded_dic["options"]["instructionset"] = EclipseStCube.get_instructionset_gnuarmeclipse_id("")
        expanded_dic["options"]["fpuabi"] = EclipseStCube.get_fpuabi_gnuarmeclipse_id("")
        expanded_dic["options"]["fpu"] = EclipseStCube.get_mfpu_gnuarmeclipse_id("")
        expanded_dic["options"]["unalignedaccess"] = EclipseStCube.get_unalignedaccess_gnuarmeclipse_id("")
        
        for name in ["common", "ld", "c", "cxx", "asm"] :
            for flag in expanded_dic['flags'][name] :
                if flag.startswith("-O") :
                    expanded_dic["options"]["optimization"] = EclipseStCube.get_optimization_gnuarmeclipse_id(flag)
                elif flag.startswith("-ggdb") :
                    pass
                elif flag.startswith("-g") :
                    expanded_dic["options"]["debug"] = EclipseStCube.get_debug_gnuarmeclipse_id(flag)
                elif flag.startswith("-mcpu=") :
                    expanded_dic["options"]["mcu"] = EclipseStCube.get_mcpu_gnuarmeclipse_id(flag)
                elif flag in ["-mthumb", "-marm"] :
                    expanded_dic["options"]["instructionset"] = EclipseStCube.get_instructionset_gnuarmeclipse_id(flag)
                elif flag.startswith("-mfloat-abi=") :
                    expanded_dic["options"]["fpuabi"] = EclipseStCube.get_fpuabi_gnuarmeclipse_id(flag)
                elif flag.startswith("-mfpu=") :
                    expanded_dic["options"]["fpu"] = EclipseStCube.get_mfpu_gnuarmeclipse_id(flag)
                elif flag in ["-munaligned-access","-mno-unaligned-access"]:
                    expanded_dic["options"]["unalignedaccess"] = EclipseStCube.get_unalignedaccess_gnuarmeclipse_id(flag)
                elif flag.replace(" ","") in self.GNU_MCU_ARM_BOOL_COMMAND2OPTIONS:
                    self.GNU_MCU_ARM_BOOL_COMMAND2OPTIONS[flag.replace(" ","")] = "true"
                elif flag.replace(" ","") in self.GNU_MCU_ARM_STR_COMMAND2OPTIONS:
                    self.GNU_MCU_ARM_BOOL_COMMAND2OPTIONS[flag.replace(" ","")] = flag
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

        expanded_dic["options"]["value"] = self.GNU_MCU_ARM_BOOL_COMMAND2OPTIONS
        expanded_dic["options"]["value"].update(self.GNU_MCU_ARM_STR_COMMAND2OPTIONS)

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
        
        # Get Enviroment TARGET_ST_CUBE
        expanded_dic["target_st_cube"] = os.environ.get("TARGET_ST_CUBE")

        project_path, output['files']['cproj'] = self.gen_file_jinja(
            'st_cube_eclipse.arm.elf.cproject.tmpl', expanded_dic, '.cproject', expanded_dic['output_dir']['path'])

        expanded_dic["addition_natures"] = """
        <nature>com.st.stm32cube.ide.mcu.MCUProjectNature</nature>
		<nature>com.st.stm32cube.ide.mcu.MCUCubeIdeServicesRevAProjectNature</nature>
		<nature>com.st.stm32cube.ide.mcu.MCUManagedMakefileProjectNature</nature>
		<nature>com.st.stm32cube.ide.mcu.MCUSingleCpuProjectNature</nature>
        """
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

