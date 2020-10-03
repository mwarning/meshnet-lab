#!/usr/bin/env python3

import datetime
import argparse
import subprocess
import hashlib
import json
import math
import time
import sys
import os

from shared import (
    eprint, wait_for_completion, exec, default_remotes, check_access,
    millis, get_remote_mapping, stop_all_terminals, format_duration,
    get_current_state, Remote
)

verbosity = 'normal'


def _get_update(to_state, remotes):
    (from_state, rmap) = get_current_state(remotes)

    if to_state == None:
        to_state = {}
    elif isinstance(to_state, str):
        with open(to_state) as file:
            to_state = json.load(file)

    def get_id_set(state):
        nodes = set()

        if state is not None:
            for link in state.get('links', []):
                nodes.add(str(link['source']))
                nodes.add(str(link['target']))

            for node in state.get('nodes', []):
                nodes.add(str(node['id']))

        return nodes

    from_ids = get_id_set(from_state)
    to_ids = get_id_set(to_state)

    a = from_ids.difference(to_ids)
    b = to_ids.difference(from_ids)

    # (old_ids, new_ids)
    return (a, b, rmap)

'''
Distribute files to different remotes
'''
def copy(remotes, source, destination):
    if isinstance(source, list):
        source = ' '.join(source)

    for remote in remotes:
        if remote.address:
            if remote.ifile:
                os.system(f'scp -r -P {remote.port} -i {remote.ifile} {source} root@{remote.address}:{destination} > /dev/null')
            else:
                os.system(f'scp -r -P {remote.port} {source} root@{remote.address}:{destination} > /dev/null')
        else:
            # local terminal
            os.system(f'cp -r {source} {destination}')

def _exec_verbose(remote, cmd, ignore_error=False):
    if verbosity == 'verbose':
        stdout, stderr, rcode = exec(remote, cmd, get_output=True, ignore_error=ignore_error, add_quotes=False)

        if len(stdout) > 0:
            sys.stdout.write(stdout)

        if len(stderr) > 0:
            sys.stderr.write(stderr)
    else:
        exec(remote, cmd, get_output=False, ignore_error=ignore_error, add_quotes=False)

def _stop_protocol(protocol, rmap, ids):
    base = os.path.dirname(os.path.realpath(__file__))
    path = f'{base}/protocols/{protocol}_stop.sh'

    if not os.path.isfile(path):
        eprint(f'File does not exist: {path}')
        stop_all_terminals()
        exit(1)

    for id in ids:
        remote = rmap[id]

        label = remote.address or 'local'
        cmd = f'ip netns exec ns-{id} sh -s {label} {id} < {path}'

        _exec_verbose(remote, cmd)

    wait_for_completion()

def _start_protocol(protocol, rmap, ids):
    base = os.path.dirname(os.path.realpath(__file__))
    path = f'{base}/protocols/{protocol}_start.sh'

    if not os.path.isfile(path):
        eprint(f'File does not exist: {path}')
        stop_all_terminals()
        exit(1)

    for id in ids:
        remote = rmap[id]

        label = remote.address or 'local'
        cmd = f'ip netns exec ns-{id} sh -s {label} {id} < {path}'

        _exec_verbose(remote, cmd)

    wait_for_completion()

def clear(remotes):
    base = os.path.dirname(os.path.realpath(__file__))

    names = []
    for name in os.listdir(f'{base}/protocols/'):
        if name.endswith('_stop.sh'):
            names.append(name)

    for remote in remotes:
        for name in names:
            label = remote.address or 'local'
            cmd = f'sh -s {label} < {base}/protocols/{name}'
            _exec_verbose(remote, cmd, ignore_error=True)

    wait_for_completion()

def stop(protocol, remotes=default_remotes):
    rmap = get_remote_mapping(remotes)
    ids = list(rmap.keys())
    _stop_protocol(protocol, rmap, ids)

def start(protocol, remotes=default_remotes):
    rmap = get_remote_mapping(remotes)
    ids = list(rmap.keys())
    _start_protocol(protocol, rmap, ids)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbosity', choices=['verbose', 'normal', 'quiet'], default='normal', help='Set verbosity.')
    parser.add_argument('--remotes', help='Distribute nodes and links on remotes described in the JSON file.')
    parser.set_defaults(to_state=None)

    subparsers = parser.add_subparsers(dest='action', required=True, help='Action')

    parser_start = subparsers.add_parser('start', help='Run start script in every namespace.')
    parser_start.add_argument('protocol', help='Routing protocol script prefix.')
    parser_start.add_argument('to_state', nargs='?', default=None, help='To state')

    parser_stop = subparsers.add_parser('stop', help='Run stop script in every namespace.')
    parser_stop.add_argument('protocol', help='Routing protocol script prefix.')
    parser_stop.add_argument('to_state', nargs='?', default=None, help='To state')

    parser_change = subparsers.add_parser('apply', help='Run stop/start scripts in every namespace.')
    parser_change.add_argument('protocol', help='Routing protocol script prefix.')
    parser_change.add_argument('to_state', nargs='?', default=None, help='To state')

    parser_run = subparsers.add_parser('run', help='Execute any command in every namespace.')
    parser_run.add_argument('command', nargs=argparse.REMAINDER,
        help='Shell command that is run. Remote address and namespace id is added to call arguments.')
    parser_run.add_argument('to_state', nargs='?', default=None, help='To state')

    parser_copy = subparsers.add_parser('copy', help='Copy to all remotes.')
    parser_copy.add_argument('source', nargs='+')
    parser_copy.add_argument('destination')

    parser_clear = subparsers.add_parser('clear', help='Run all stop scripts in every namespaces.')

    args = parser.parse_args()

    if args.remotes:
        if not os.path.isfile(args.remotes):
            eprint(f'File not found: {args.remotes}')
            stop_all_terminals()
            exit(1)

        with open(args.remotes) as file:
            args.remotes = [Remote.from_json(obj) for obj in json.load(file)]
    else:
        args.remotes = default_remotes

    check_access(args.remotes)

    global verbosity
    verbosity = args.verbosity

    # get nodes that have been added or will be removed
    (old_ids, new_ids, rmap) = _get_update(args.to_state, args.remotes)

    if args.action == 'start':
        ids = new_ids if args.to_state else list(rmap.keys())

        beg_ms = millis()
        _start_protocol(args.protocol, rmap, ids)
        end_ms = millis()

        if verbosity != 'quiet':
            print('started {} in {} namespaces in {}'.format(args.protocol, len(ids), format_duration(end_ms - beg_ms)))
    elif args.action == 'stop':
        ids = old_ids if args.to_state else list(rmap.keys())

        beg_ms = millis()
        _stop_protocol(args.protocol, rmap, ids)
        end_ms = millis()

        if verbosity != 'quiet':
            print('stopped {} in {} namespaces in {}'.format(args.protocol, len(ids), format_duration(end_ms - beg_ms)))
    elif args.action == 'apply':
        beg_ms = millis()
        _stop_protocol(args.protocol, rmap, old_ids)
        _start_protocol(args.protocol, rmap, new_ids)
        end_ms = millis()

        if verbosity != 'quiet':
            print('applied {} in {} namespaces in {}'.format(args.protocol, len(rmap.keys()), format_duration(end_ms - beg_ms)))
    elif args.action == 'clear':
        beg_ms = millis()
        clear(args.remotes)
        end_ms = millis()

        if verbosity != 'quiet':
            print('cleared on {} remotes in {}'.format(len(args.remotes), format_duration(end_ms - beg_ms)))
    elif args.action == 'copy':
        beg_ms = millis()
        copy(args.remotes, args.source, args.destination)
        end_ms = millis()

        if verbosity != 'quiet':
            print('copied on {} remotes in {}'.format(len(args.remotes), format_duration(end_ms - beg_ms)))
    elif args.action == 'run':
        ids = new_ids if args.to_state else list(rmap.keys())

        for id in ids:
            remote = rmap[id]
            label = remote.address or 'local'
            cmd = f'ip netns exec ns-{id} {" ".join(args.command)} {label} {id}'
            _exec_verbose(remote, cmd)
    else:
        eprint('Unknown action: {}'.format(args.action))
        stop_all_terminals()
        exit(1)

    stop_all_terminals()

if __name__ == "__main__":
    main()
