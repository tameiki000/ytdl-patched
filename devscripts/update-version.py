#!/usr/bin/env python3

# Allow direct execution
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


import argparse
import contextlib
import sys
from datetime import datetime

from devscripts.utils import read_version, run_process, write_file


def get_new_version(version, revision):
    time = datetime.utcnow()
    build_time = time.strftime('%s')
    if not version:
        version = time.strftime('%Y.%m.%d.%s')

    if revision:
        assert revision.isdigit(), 'Revision must be a number'
    else:
        old_version = read_version().split('.')
        version_tuple = version.split('.')
        if version_tuple == old_version:
            # increment the last value so that we won't make duplicate version
            build_time = str(int((old_version + [0])[3]) + 1)
            version = '.'.join(version_tuple[:3] + [build_time])

    return (f'{version}.{revision}' if revision else version), build_time


def get_git_head():
    with contextlib.suppress(Exception):
        return run_process('git', 'rev-parse', 'HEAD').stdout.strip()


VERSION_TEMPLATE = '''\
# Autogenerated by devscripts/update-version.py

__version__ = {version!r}

RELEASE_GIT_HEAD = {git_head!r}

VARIANT = None

UPDATE_HINT = None

CHANNEL = {channel!r}
'''

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Update the version.py file')
    parser.add_argument(
        '-c', '--channel', choices=['stable', 'nightly'], default='stable',
        help='Select update channel (default: %(default)s)')
    parser.add_argument(
        '-o', '--output', default='yt_dlp/version.py',
        help='The output file to write to (default: %(default)s)')
    parser.add_argument(
        'version', nargs='?', default=None,
        help='A version or revision to use instead of generating one')
    args = parser.parse_args()

    git_head = get_git_head()

    version, build_time = (
        (args.version, datetime.utcnow().strftime('%s')) if args.version and '.' in args.version
        else get_new_version(None, args.version))
    normalized_version = '.'.join(str(int(x)) for x in version.split('.'))
    write_file(args.output, VERSION_TEMPLATE.format(
        version=version, git_head=git_head, channel=args.channel))
    github_output = os.getenv('GITHUB_OUTPUT')
    if github_output:
        write_file(github_output, f'ytdlp_version={version}\n', 'a')
        write_file(github_output, f'latest_version={version}\n', 'a')
        write_file(github_output, f'latest_version_normalized={normalized_version}\n', 'a')
        write_file(github_output, f'latest_version_numeric={build_time}\n', 'a')

    print(f'version={version} ({args.channel}), head={git_head}')
