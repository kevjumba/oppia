# Copyright 2020 The Oppia Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Installation script for Oppia python backend libraries."""

from __future__ import absolute_import  # pylint: disable=import-only-modules
from __future__ import unicode_literals  # pylint: disable=import-only-modules

import collections
import os
from pip._internal.utils import misc
import pkg_resources
import shutil
import subprocess
import sys

import python_utils
from scripts import common


THIRD_PARTY_DIR = os.path.join('.', 'third_party')
THIRD_PARTY_STATIC_DIR = os.path.join(THIRD_PARTY_DIR, 'static')

PIP_TOOLS_DIR = os.path.join(
    common.OPPIA_TOOLS_DIR, 'pip-tools-%s' % common.PIP_TOOLS_VERSION)

# TODO: WHy we don't care about the pip version on the developers local machine?


def _get_requirements_file_contents():
    requirements_contents = collections.defaultdict()
    with python_utils.open_file(common.REQUIREMENTS_FILE_PATH, 'r') as f:
        lines = f.readlines()
        for l in lines:
            if l.startswith('#'):
                continue
            library_and_version = l.split(' ')[0].split('==')
            library = library_and_version[0].lower()
            version = library_and_version[1]
            requirements_contents[library] = version

    return requirements_contents


def _get_third_party_directory_contents():
    installed_distributions = misc.get_installed_distributions(
        skip=[], paths=[common.THIRD_PARTY_PYTHON_LIBS_DIR])
    directory_contents = collections.defaultdict()
    for d in installed_distributions:
        library_and_version = python_utils.convert_to_bytes(d).split(' ')
        library = library_and_version[0].lower()
        version = library_and_version[1]
        directory_contents[library] = version

    return directory_contents


def get_mismatches():
    requirements_contents = _get_requirements_file_contents()
    directory_contents = _get_third_party_directory_contents()

    mismatches = {}
    for library in requirements_contents:
        # Library exists in the directory and the requirements file.
        if library in directory_contents:
            # Library and version match.
            if directory_contents[library] == requirements_contents[library]:
                continue
            # Library matches but version doesn't match.
            else:
                mismatches[library] = (
                    requirements_contents[library], directory_contents[library])
        # Library exists in the requirements file but not in the directory.
        else:
            mismatches[library] = (requirements_contents[library], None)

    for library in directory_contents:
        # Library exists in the directory but is not in the requirements file.
        if library not in requirements_contents:
            mismatches[library] = (None, directory_contents[library])

    return mismatches


def _remove_metadata(library, version):
    # The possible strings that a metadata directory or file name can
    # start with.
    possible_filename_start_strings = [
        '%s-%s' % (library, version),
        # Some metadata folders replace the hyphens with underscores.
        '%s-%s' % (library.replace('-', '_'), version)
    ]
    for f in os.listdir(common.THIRD_PARTY_PYTHON_LIBS_DIR):
        if (f.startswith(possible_filename_start_strings[0]) or
                f.startswith(possible_filename_start_strings[1])):
            to_delete_path = os.path.join(
                common.THIRD_PARTY_PYTHON_LIBS_DIR, f)
            if os.path.isdir(to_delete_path):
                shutil.rmtree(to_delete_path)
            else:
                os.remove(to_delete_path)


def _rectify_third_party_directory(mismatches):
    # Handling 5 or more mismatches requires 5 or more individual `pip install`
    # commands which is slower than just reinstalling all of the libraries using
    # `pip install -r requirements.txt`.
    if len(mismatches) >= 5:
        if os.path.isdir(common.THIRD_PARTY_PYTHON_LIBS_DIR):
            shutil.rmtree(common.THIRD_PARTY_PYTHON_LIBS_DIR)
        subprocess.check_call([
            'pip', 'install', '--target',
            common.THIRD_PARTY_PYTHON_LIBS_DIR,
            '--no-dependencies', '-r',
            common.REQUIREMENTS_FILE_PATH
        ])
        return

    for library, versions in mismatches.items():
        requirements_version = (
            pkg_resources.parse_version(versions[0]) if versions[0] else None)
        directory_version = (
            pkg_resources.parse_version(versions[1]) if versions[1] else None)

        # Library is installed in the directory but not listed in
        # requirements.
        if not requirements_version:
            shutil.rmtree(common.THIRD_PARTY_PYTHON_LIBS_DIR)
            subprocess.check_call([
                'pip', 'install', '--target',
                common.THIRD_PARTY_PYTHON_LIBS_DIR,
                '--no-dependencies', '-r',
                common.REQUIREMENTS_FILE_PATH
            ])

        # Library exists in requirements but not in the directory or the
        # currently installed library version is not up-to-date with the
        # required 'requirements.txt' version.
        elif (not directory_version or
              requirements_version > directory_version):
            subprocess.check_call([
                'pip', 'install', '--target',
                common.THIRD_PARTY_PYTHON_LIBS_DIR,
                '--no-dependencies',
                '%s==%s' % (
                    library,
                    python_utils.convert_to_bytes(requirements_version)),
                '--upgrade'
            ])
        # The currently installed library version is higher than the required
        # 'requirements.txt' version.
        elif requirements_version < directory_version:
            subprocess.check_call([
                'pip', 'install', '--target',
                common.THIRD_PARTY_PYTHON_LIBS_DIR,
                '--no-dependencies',
                '%s==%s' % (
                    library,
                    python_utils.convert_to_bytes(requirements_version)),
                '--upgrade'
            ])
            _remove_metadata(
                library, python_utils.convert_to_bytes(directory_version))


def main():
    sys.path.insert(0, os.path.join(
        common.OPPIA_TOOLS_DIR, 'pip-tools-%s' % common.PIP_TOOLS_VERSION))
    python_utils.PRINT('Regenerating "requirements.txt" file...')
    subprocess.check_call(
        ['python', '-m', 'scripts.regenerate_requirements'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    mismatches = get_mismatches()
    if mismatches:
        _rectify_third_party_directory(mismatches)
    else:
        python_utils.PRINT(
            'Third party python libraries already installed correctly.')

# The 'no coverage' pragma is used as this line is un-testable. This is because
# it will only be called when install_third_party_libs.py is used as a script.
if __name__ == '__main__': # pragma: no cover
    main()
