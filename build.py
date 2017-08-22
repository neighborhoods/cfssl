#!/usr/bin/env python3
# -*- coding: utf-8 -*-

###############################################################################
# MIT LICENSE
# Copyright (c) 2017 Neigborhoods.com, LLC
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# allcopies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
###############################################################################

import itertools
import os
import shutil
import subprocess
import tarfile

GIT_PATH = shutil.which('git')
CFSSL_REPO = 'https://github.com/cloudflare/cfssl.git'
CFSSL_VERSION = '1.2.0'
CFSSL_BUILD_SCRIPT = 'script/build'
ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
DIST_PATH = os.path.join(ROOT_PATH, 'dist')
REPO_PATH = os.path.join(ROOT_PATH, 'cfssl')
REPO_CMD_PATH = os.path.join(REPO_PATH, 'cmd')
REPO_DIST_PATH = os.path.join(REPO_PATH, 'dist')
DIST_PATH = os.path.join(ROOT_PATH, 'dist', CFSSL_VERSION)

OS = [
    # 'darwin', # See https://github.com/cloudflare/cfssl/issues/778
    'linux',
    'windows',
]

ARCH = [
    '386',
    'amd64',
    'arm',
    'ppc64le',
]

# These builds are not valid targets
SKIP_BUILDS = [
    ('windows', 'arm'),
    ('windows', 'ppc64le'),
]

def archive(dist):
    if not os.path.isdir(DIST_PATH):
        os.makedirs(DIST_PATH)

    tar_name = dist_name(dist)
    print('Creating dist {}'.format(tar_name))

    tar_path = dist_path(tar_name)
    tar_file = tarfile.open(
        name=tar_path,
        mode='w',
    )

    with tar_file:
        for exec_ in executables():
            exec_path = executable_path(*dist, exec_)
            exec_ = os_name(dist[0], exec_)

            print('  Adding {}'.format(exec_))
            tar_file.add(exec_path, arcname=exec_)

def build(dist):
    os_, arch = dist

    cmd = [
        os.path.join(REPO_PATH, CFSSL_BUILD_SCRIPT),
        '-os={}'.format(os_),
        '-arch={}'.format(arch),
    ]

    print('Calling %s' % ' '.join(cmd))
    subprocess.run(cmd, check=True, cwd=REPO_PATH)

def build_dists(dists_to_build):
    if not dists_to_build:
        print('Nothing to build')
        return

    print('Building:\n  %s' % '\n  '.join(
        [
            '{}-{}'.format(os_, arch)
            for os_, arch in dists_to_build
        ]
    ))

    for dist in dists_to_build:
        clean(dist)

    for dist in dists_to_build:
        build(dist)
        archive(dist)

def checkout_version():
    print('Checking out version {}'.format(CFSSL_VERSION))

    cmd = [
        GIT_PATH,
        'checkout',
        CFSSL_VERSION,
    ]

    subprocess.run(cmd, check=True, cwd=REPO_PATH)

def clean(dist):
    tar_path = dist_path(dist)
    try:
        os.remove(tar_path)
    except:
        pass

def clone_repo():
    print('Cloning {} to {}'.format(CFSSL_REPO, REPO_PATH))

    cmd = [
        GIT_PATH,
        'clone',
        CFSSL_REPO,
        REPO_PATH,
    ]

    subprocess.run(cmd, check=True)

def dists():
    '''
    Generator for tuples of distributions in form of (os, arch)
    '''
    for os_, arch in itertools.product(OS, ARCH):
        if (os_, arch) in SKIP_BUILDS:
            continue

        yield (os_, arch)

def executables():
    '''
    Generator for list of output executables.
    Determined by the cfssl/cmd directory members.
    '''
    for entry in os.listdir(REPO_CMD_PATH):
        if os.path.isdir(os.path.join(REPO_CMD_PATH, entry)):
            yield entry

def executable_name(os_, arch, exec_):
    '''
    Name of the executable generated during the cfssl build
    '''
    name = '{}_{}-{}'.format(
        exec_,
        os_,
        arch,
    )

    return os_name(os_, name)

def executable_path(*args):
    return os.path.join(REPO_DIST_PATH, executable_name(*args))

def dist_has_all(dist):
    '''
    Return True if the dist has all the right files in it, false otherwise
    '''
    tar_path = dist_path(dist)
    try:
        tar_file = tarfile.open(
            name=tar_path,
            mode='r',
        )
    except tarfile.ReadError:
        return False

    with tar_file:
        names = tar_file.getnames()

    for exec_ in executables():
        exec_ = os_name(dist[0], exec_)
        if exec_ not in names:
            return False

    return True

def dist_name(dist):
    '''
    Return the name of the tarfile that we output ourselves
    '''
    os_, arch = dist
    return 'cfssl-{}-{}.tar'.format(
        os_,
        arch,
    )

def dist_path(dist):
    if isinstance(dist, str):
        name = dist
    else:
        name = dist_name(dist)

    return os.path.join(DIST_PATH, name)

def has_dist(dist):
    return os.path.isfile(dist_path(dist))

def missing_dists():
    '''
    Generator for list of distributions that we need to build
    '''
    for dist in dists():
        if not has_dist(dist) or not dist_has_all(dist):
            yield dist

def os_name(os_, exec_):
    '''
    Some OS's (*cough* Windows *cough*) need a suffix on the exec name.
    Returns the executable's name formatted for that OS
    '''

    if os_ == 'windows':
        return exec_ + '.exe'

    return exec_

def main():
    if not GIT_PATH:
        raise ValueError('No git on our path')

    os.chdir(ROOT_PATH)

    if not os.path.isdir(REPO_PATH):
        clone_repo()

    checkout_version()

    dists_to_build = list(missing_dists())
    build_dists(dists_to_build)


if __name__ == '__main__':
    main()
