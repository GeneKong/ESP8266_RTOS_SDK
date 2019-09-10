# Copyright 2015 0xc0170
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

import logging
import copy
import os
import uuid
import xmltodict
from collections import OrderedDict

from .tool import Tool, Exporter
from .gcc import MakefileGcc
from ..util import SOURCE_KEYS

logger = logging.getLogger('progen.tools.visual_studio')

# This file contains 2 classes, VisualStudio gdb project and VisualStudio with gdb project configured for arm gcc
# I recommend doing minimal project when parsing to python. For instance, we just need one source file, one macro , one header file, or
# any other data for progen. To get the syntax, where to inject those data and the syntax. Then we can just loop to get data injected.

class VisualStudioGDB(Tool, Exporter):

    # Asset - linux_nmake.xaml
    linux_nmake_xaml = OrderedDict([('Rule', OrderedDict([('@Name', 'ConfigurationNMake'), ('@DisplayName', 'NMake'), ('@PageTemplate', 'generic'), ('@Description', 'NMake'), ('@SwitchPrefix', '/'), ('@Order', '100'), ('@xmlns', 'http://schemas.microsoft.com/build/2009/properties'), ('Rule.Categories', OrderedDict([('Category', [OrderedDict([('@Name', 'General'), ('@DisplayName', 'General'), ('@Description', 'General')]), OrderedDict([('@Name', 'IntelliSense'), ('@DisplayName', 'IntelliSense'), ('@Description', 'IntelliSense')])])])), ('Rule.DataSource', OrderedDict([('DataSource', OrderedDict([('@Persistence', 'ProjectFile')]))])), ('StringProperty', [OrderedDict([('@Name', 'NMakeBuildCommandLine'), ('@DisplayName', 'Build Command Line'), ('@Description', "Specifies the command line to run for the 'Build' command."), ('@IncludeInCommandLine', 'false'), ('@Category', 'General'), ('@F1Keyword', 'VC.Project.VCNMakeTool.BuildCommandLine'), ('StringProperty.ValueEditors', OrderedDict([('ValueEditor', OrderedDict([('@EditorType', 'DefaultCommandPropertyEditor'), ('@DisplayName', '<Edit...>')]))]))]), OrderedDict([('@Name', 'NMakeReBuildCommandLine'), ('@DisplayName', 'Rebuild All Command Line'), ('@Description', "Specifies the command line to run for the 'Rebuild All' command."), ('@IncludeInCommandLine', 'false'), ('@Category', 'General'), ('@F1Keyword', 'VC.Project.VCNMakeTool.ReBuildCommandLine'), ('StringProperty.ValueEditors', OrderedDict([('ValueEditor', OrderedDict([('@EditorType', 'DefaultCommandPropertyEditor'), ('@DisplayName', '<Edit...>')]))]))]), OrderedDict([('@Name', 'NMakeCleanCommandLine'), ('@DisplayName', 'Clean Command Line'), ('@Description', "Specifies the command line to run for the 'Clean' command."), ('@IncludeInCommandLine', 'false'), ('@Category', 'General'), ('@F1Keyword', 'VC.Project.VCNMakeTool.CleanCommandLine'), ('StringProperty.ValueEditors', OrderedDict([('ValueEditor', OrderedDict([('@EditorType', 'DefaultCommandPropertyEditor'), ('@DisplayName', '<Edit...>')]))]))]), OrderedDict([('@Name', 'NMakeOutput'), ('@DisplayName', 'Output'), ('@Description', 'Specifies the output file to generate.'), ('@Category', 'General'), ('@IncludeInCommandLine', 'false'), ('@F1Keyword', 'VC.Project.VCNMakeTool.Output')]), OrderedDict([('@Name', 'AdditionalOptions'), ('@DisplayName', 'Additional Options'), ('@Category', 'IntelliSense'), ('@Description', 'Specifies additional compiler switches to be used by Intellisense when parsing C++ files')])]), ('StringListProperty', [OrderedDict([('@Name', 'NMakePreprocessorDefinitions'), ('@DisplayName', 'Preprocessor Definitions'), ('@Category', 'IntelliSense'), ('@Switch', 'D'), ('@Description', 'Specifies the preprocessor defines used by the source files.'), ('@F1Keyword', 'VC.Project.VCNMakeTool.PreprocessorDefinitions')]), OrderedDict([('@Name', 'NMakeIncludeSearchPath'), ('@DisplayName', 'Include Search Path'), ('@Category', 'IntelliSense'), ('@Switch', 'I'), ('@Description', 'Specifies the include search path for resolving included files.'), ('@Subtype', 'folder'), ('@F1Keyword', 'VC.Project.VCNMakeTool.IncludeSearchPath')]), OrderedDict([('@Name', 'NMakeForcedIncludes'), ('@DisplayName', 'Forced Includes'), ('@Category', 'IntelliSense'), ('@Switch', 'FI'), ('@Description', 'Specifies the files that are forced included.'), ('@Subtype', 'folder'), ('@F1Keyword', 'VC.Project.VCNMakeTool.ForcedIncludes')]), OrderedDict([('@Name', 'NMakeAssemblySearchPath'), ('@DisplayName', 'Assembly Search Path'), ('@Category', 'IntelliSense'), ('@Switch', 'AI'), ('@Description', 'Specifies the assembly search path for resolving used .NET assemblies.'), ('@Subtype', 'folder'), ('@F1Keyword', 'VC.Project.VCNMakeTool.AssemblySearchPath')]), OrderedDict([('@Name', 'AdditionalSOSearchPaths'), ('@DisplayName', 'Additional Symbol Search Paths'), ('@Category', 'IntelliSense'), ('@Description', 'Locations to identify '), ('@F1Keyword', 'VC.Project.VCNMakeTool.AdditionalSOSearchPaths')])])]))])

    # Asset LocalDebugger.xaml
    linux_debugger_xaml = OrderedDict([('Rule', OrderedDict([('@Name', 'LocalDebugger'), ('@DisplayName', 'Local GDB'), ('@PageTemplate', 'debugger'), ('@Order', '200'), ('@Description', 'Debugger options'), ('@xmlns:sys', 'clr-namespace:System;assembly=mscorlib'), ('@xmlns:x', 'http://schemas.microsoft.com/winfx/2006/xaml'), ('@xmlns', 'http://schemas.microsoft.com/build/2009/properties'), ('Rule.DataSource', OrderedDict([('DataSource', OrderedDict([('@Persistence', 'UserFile')]))])), ('Rule.Categories', OrderedDict([('Category', OrderedDict([('@Name', 'StartOptions'), ('@DisplayName', 'Start Options'), ('@Description', 'Start Options')]))])), ('StringProperty', [OrderedDict([('@Name', 'LocalWorkingDirectory'), ('@DisplayName', 'Local Working Directory'), ('@Description', 'Local root location where executable runs'), ('@F1Keyword', 'VC.Project.LinuxDebugger.PackagePath'), ('StringProperty.ValueEditors', OrderedDict([('ValueEditor', [OrderedDict([('@EditorType', 'DefaultStringPropertyEditor'), ('@DisplayName', '<Edit...>')]), OrderedDict([('@EditorType', 'DefaultFolderPropertyEditor'), ('@DisplayName', '<Browse...>')])])]))]), OrderedDict([('@Name', 'LocalExecutable'), ('@DisplayName', 'Local Executable'), ('@Description', 'Name of the local executable program'), ('@F1Keyword', 'VC.Project.LinuxDebugger.PackagePath')]), OrderedDict([('@Name', 'LocalExecutableArguments'), ('@DisplayName', 'Local Executable Arguments'), ('@Description', 'Optional, arguments to pass to the local executable'), ('@F1Keyword', 'VC.Project.LinuxDebugger.PackagePath')]), OrderedDict([('@Name', 'LocalDebuggerExecutable'), ('@DisplayName', 'Local Debugger Executable'), ('@Description', 'Full path to local gdb/lldb executable'), ('@F1Keyword', 'VC.Project.LinuxDebugger.PackagePath'), ('StringProperty.ValueEditors', OrderedDict([('ValueEditor', [OrderedDict([('@EditorType', 'DefaultStringPropertyEditor'), ('@DisplayName', '<Edit...>')]), OrderedDict([('@EditorType', 'DefaultFilePropertyEditor'), ('@DisplayName', '<Browse...>')])])]))]), OrderedDict([('@Name', 'LocalDebuggerServerAddress'), ('@DisplayName', 'Local Debugger Server Address'), ('@Description', 'Optional, local debugger server address if needed'), ('@F1Keyword', 'VC.Project.LinuxDebugger.PackagePath')])])]))])

    # .vcxproj.user file template
    vcxproj_user_tmpl = OrderedDict([('Project', OrderedDict([('@ToolsVersion', '14.0'), ('@xmlns', 'http://schemas.microsoft.com/developer/msbuild/2003'), ('PropertyGroup', OrderedDict([('@Condition', "'$(Configuration)|$(Platform)'=='Debug|ARM'"), ('LocalExecutable', '$(WorkingDir)build\\lpc1768_blinky'), ('LocalDebuggerServerAddress', 'localhost:3333'), ('DebuggerFlavor', 'LocalDebugger'), ('LocalWorkingDirectory', 'C:\\Code\\git_repo\\github\\project_generator_mbed_examples\\projects\\visual_studio_make_gcc_arm_mbed-lpc1768\\lpc1768_blinky'), ('LocalDebuggerExecutable', 'arm-none-eabi-gdb')]))]))])

    # .vcxproj.filters file template
    vcxproj_filters_tmpl = OrderedDict([('Project', OrderedDict([('@ToolsVersion', '4.0'), ('@xmlns', 'http://schemas.microsoft.com/developer/msbuild/2003'), ('ItemGroup', [OrderedDict([('Filter', [OrderedDict([('@Include', 'Source Files'), ('UniqueIdentifier', '{08a26e93-524c-4982-a01c-c8d4f223d6be}'), ('Extensions', 'cpp;c;cc;cxx;asm;s')]), OrderedDict([('@Include', 'Header Files'), ('UniqueIdentifier', '{35c51339-ba9d-43c8-bd71-5f3199e89878}'), ('Extensions', 'h;hh;hpp;hxx;hm;inl;inc')])])]), OrderedDict([('ClCompile', OrderedDict([('@Include', ''), ('Filter', 'Source Files')]))]), OrderedDict([('ClInclude', OrderedDict([('@Include', ''), ('Filter', 'Include Files')]))])])]))])
    # vcxproj_filters_tmpl = OrderedDict([(u'http://schemas.microsoft.com/developer/msbuild/2003:Project', OrderedDict([(u'@ToolsVersion', u'4.0'), (u'http://schemas.microsoft.com/developer/msbuild/2003:ItemGroup', [OrderedDict([(u'http://schemas.microsoft.com/developer/msbuild/2003:ClCompile', [OrderedDict([(u'@Include', u'..\\..\\..\\mbed\\libraries\\mbed\\targets\\hal\\TARGET_NXP\\TARGET_LPC176X\\analogin_api.c'), (u'http://schemas.microsoft.com/developer/msbuild/2003:Filter', u'Sources')]), OrderedDict([(u'@Include', u'..\\..\\..\\mbed\\libraries\\mbed\\targets\\hal\\TARGET_NXP\\TARGET_LPC176X\\analogout_api.c'), (u'http://schemas.microsoft.com/developer/msbuild/2003:Filter', u'Sources')])])]), OrderedDict([(u'http://schemas.microsoft.com/developer/msbuild/2003:ClInclude', OrderedDict([(u'@Include', u'..\\..\\..\\mbed\\libraries\\mbed\\targets\\cmsis\\core_ca9.h')]))]), OrderedDict([(u'http://schemas.microsoft.com/developer/msbuild/2003:None', OrderedDict([(u'@Include', u'Makefile')]))]), OrderedDict([(u'http://schemas.microsoft.com/developer/msbuild/2003:Filter', OrderedDict([(u'@Include', u'Sources'), (u'http://schemas.microsoft.com/developer/msbuild/2003:UniqueIdentifier', u'{76f35112-2644-4e2a-8007-2fbb45a4edca}')]))])])]))])

    generated_project = {
        'path': '',
        'files': {
            'vcxproj.filters': '',
            'vcxproj': '',
            'vcxproj.user': '',
        }
    }

    def __init__(self, workspace, env_settings):
        self.workspace = workspace
        self.env_settings = env_settings

    @staticmethod
    def get_toolnames():
        return ['visual_studio']

    @staticmethod
    def get_toolchain():
        return None

    def _set_vcxproj(self, name='', execut='', build='', rebuild='', clean=''):
        proj_dic = {}
        proj_dic['build_command'] = build
        proj_dic['rebuild_command'] = rebuild
        proj_dic['clean_command'] = clean
        proj_dic['executable_path'] = execut
        proj_dic['uuid'] = str(uuid.uuid5(uuid.NAMESPACE_URL, name)).upper()
        return proj_dic

    def _set_vcxproj_user(self, gdb_add, debbuger_exec, local_executable, working_dir):
        vcxproj_user = copy.deepcopy(self.vcxproj_user_tmpl)
        vcxproj_user['Project']['PropertyGroup']['LocalDebuggerServerAddress'] = gdb_add
        vcxproj_user['Project']['PropertyGroup']['arm-none-eabi-gdb'] = 'arm-none-eabi-gdb'
        vcxproj_user['Project']['PropertyGroup']['LocalExecutable'] = local_executable
        vcxproj_user['Project']['PropertyGroup']['LocalWorkingDirectory'] = working_dir
        return vcxproj_user

    def _generate_vcxproj_files(self, proj_dict, name, rel_path, vcxproj_user_dic):
        output = copy.deepcopy(self.generated_project)
        project_path, output['files']['vcxproj.filters'] = self.gen_file_jinja(
            'visual_studio.vcxproj.filters.tmpl', proj_dict, '%s.vcxproj.filters' % name, rel_path)
        project_path, output['files']['vcxproj'] = self.gen_file_jinja(
            'visual_studio.vcxproj.tmpl', proj_dict, '%s.vcxproj' % name, rel_path)
        project_path, output['files']['vcxproj.user'] = self.gen_file_raw(
            xmltodict.unparse(vcxproj_user_dic, pretty=True), '%s.vcxproj.user' % name, rel_path)
        return project_path, output

    def _set_groups(self, proj_dic):
        # each group needs to have own filter with UUID
        proj_dic['source_groups'] = {}
        proj_dic['include_groups'] = {}
        for key in SOURCE_KEYS:
            for group_name, files in list(proj_dic[key].items()):
                proj_dic['source_groups'][group_name] = str(uuid.uuid5(uuid.NAMESPACE_URL, group_name)).upper()
        for k,v in list(proj_dic['include_files'].items()):
            proj_dic['include_groups'][k] = str(uuid.uuid5(uuid.NAMESPACE_URL, k)).upper()

    def export_project(self):
        output = copy.deepcopy(self.generated_project)
        expanded_dic = self.workspace.copy()

        # data for .vcxproj
        expanded_dic['vcxproj'] = {}
        expanded_dic['vcxproj'] = self._set_vcxproj(expanded_dic['name'])

        # data for debugger for pyOCD
        expanded_dic['vcxproj_user'] = {}
        # TODO: localhost and gdb should be misc for VS ! Add misc options
        vcxproj_user_dic = self._set_vcxproj_user('localhost:3333', 'arm-none-eabi-gdb',
            os.path.join(expanded_dic['build_dir'], expanded_dic['name']), os.path.join(os.getcwd(), expanded_dic['output_dir']['path']))

        self._set_groups(expanded_dic)

        # Project files
        project_path, output = self._generate_vcxproj_files(expanded_dic, 
            expanded_dic['name'], expanded_dic['output_dir']['path'], vcxproj_user_dic)

        # NMake and debugger assets
        # TODO: not sure about base class having NMake and debugger. We might want to disable that by default?
        self.gen_file_raw(xmltodict.unparse(self.linux_nmake_xaml, pretty=True), 'linux_nmake.xaml', expanded_dic['output_dir']['path'])
        self.gen_file_raw(xmltodict.unparse(self.linux_debugger_xaml, pretty=True), 'LocalDebugger.xaml', expanded_dic['output_dir']['path'])

        return output

    def export_workspace(self):
        logger.debug("Not supported currently")

    def get_generated_project_files(self):
        return {'path': self.workspace['path'], 'files': [self.workspace['files']['vcxproj.filters'],
            self.workspace['files']['vcxproj'], self.workspace['files']['vcxproj.user']]}

class VisualStudioMakeGCCARM(VisualStudioGDB):

    generated_project = {
        'path': '',
        'files': {
            'vcxproj.filters': '',
            'vcxproj': '',
            'vcxproj.user': '',
            'makefile': '',
        }
    }

    def __init__(self, workspace, env_settings):
        super(VisualStudioMakeGCCARM, self).__init__(workspace, env_settings)
        self.exporter = MakefileGcc(workspace, env_settings)

    @staticmethod
    def get_toolnames():
        return VisualStudioGDB.get_toolnames() + MakefileGcc.get_toolnames()

    @staticmethod
    def get_toolchain():
        return MakefileGcc.get_toolchain()

    def export_project(self):
        output = copy.deepcopy(self.generated_project)
        data_for_make = self.workspace.copy()

        self.exporter.process_data_for_makefile(data_for_make)
        output['path'], output['files']['makefile'] = self.gen_file_jinja('makefile_gcc.tmpl', data_for_make, 'Makefile', data_for_make['output_dir']['path'])

        expanded_dic = self.workspace.copy()

        expanded_dic['makefile'] = True

        # data for .vcxproj
        expanded_dic['vcxproj'] = {}
        expanded_dic['vcxproj'] = self._set_vcxproj(expanded_dic['name'],'make all', 'make clean &amp;&amp; make all',
            'make clean &amp;&amp; make all', '')

        # data for debugger for pyOCD
        expanded_dic['vcxproj_user'] = {}
        # TODO: localhost and gdb should be misc for VS ! Add misc options
        vcxproj_user_dic = self._set_vcxproj_user('localhost:3333', 'arm-none-eabi-gdb',
            os.path.join(expanded_dic['build_dir'], expanded_dic['name']), os.path.join(os.getcwd(), data_for_make['output_dir']['path']))

        self._set_groups(expanded_dic)

        # Project files
        project_path, vcx_files = self._generate_vcxproj_files(expanded_dic, expanded_dic['name'], 
            data_for_make['output_dir']['path'], vcxproj_user_dic)
        output['files']['vcxproj.filters'] = vcx_files['files']['vcxproj.filters']
        output['files']['vcxproj'] = vcx_files['files']['vcxproj']
        output['files']['vcxproj.user'] = vcx_files['files']['vcxproj.user']

        # NMake and debugger assets
        self.gen_file_raw(xmltodict.unparse(self.linux_nmake_xaml, pretty=True), 'linux_nmake.xaml', data_for_make['output_dir']['path'])
        self.gen_file_raw(xmltodict.unparse(self.linux_debugger_xaml, pretty=True), 'LocalDebugger.xaml', data_for_make['output_dir']['path'])

        return output

    def get_generated_project_files(self):
        return {'path': self.workspace['path'], 'files': [self.workspace['files']['vcxproj.filters'],
            self.workspace['files']['vcxproj'], self.workspace['files']['vcxproj.user'],
            self.workspace['files']['Makefile']]}
