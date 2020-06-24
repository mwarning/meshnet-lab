import datetime
import subprocess
import threading
import queue
import atexit
import time
import sys
import os


default_remotes = [{}] # local
terminals = {} # terminals (SSH/local)


def eprint(s):
    sys.stderr.write(s + '\n')

# get time in milliseconds
def millis():
    return int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds() * 1000)

def create_process(remote, command):
    address = remote.get('address')
    port = remote.get('port', 22)
    ifile = remote.get('identity_file')

    if address:
        # SSH terminal
        command = command.replace('\'', '\\\'') # escape '

        if ifile:
            command = f'ssh -p {port} -i {ifile} root@{address} \'{command}\''
        else:
            command = f'ssh -p {port} root@{address} \'{command}\''
    else:
        # local terminal
        command = f'{command}'

    return subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

'''
SSH or local terminal thread
for a higher execution speed
'''
class TerminalThread(threading.Thread):
    def __init__(self, remote):
        super(TerminalThread, self).__init__()
        self.remote = remote
        self.finish = False
        self.queue = queue.Queue()
        self.output_event = threading.Event()
        self.output = None
        self.start()

    def run(self):
        while True:
            try:
                self.output_event.clear()

                # might raise Empty
                (ignore_error, command) = self.queue.get(True, 1)

                p = create_process(self.remote, command)

                (std, err) = p.communicate()
                stdout = std.decode()
                errout = err.decode()

                #print('{} ({}, {}): {}'.format(self.remote.get("address"), self.queue.qsize(), ignore_error, command))

                if p.returncode != 0 and not ignore_error:
                    address = self.remote.get('address', 'local')
                    eprint(errout)
                    eprint(stdout)
                    eprint(f'Abort, command failed on {address}: {command}')
                    eprint('Network might be in an undefined state!')

                    # make sure the main thread can exit, too
                    self.output_event.set()
                    exit(1)

                if self.queue.empty():
                    self.output = (stdout, errout, p.returncode)
                    self.output_event.set()
            except queue.Empty:
                # try again or finish loop
                if self.finish:
                    break
            except Exception as e:
                eprint(e)
                # make sure the main thread can exit, too
                self.output_event.set()
                exit(1)

def exec(remote, command, get_output=False, ignore_error=False):
    i = id(remote)

    if i not in terminals:
        terminals[i] = TerminalThread(remote)

    terminals[i].queue.put((ignore_error, command))

    if get_output:
        t = terminals[i]
        t.output_event.wait()
        if t.output is None:
            exit(1)
        return t.output
    else:
        return None

'''
The open terminal threads block our
program to exit if not finished
'''
def stop_all_terminals():
    for term in terminals.values():
        term.finish = True
    for term in terminals.values():
        term.join()

def wait_for_completion():
    for term in terminals.values():
        while term.queue.qsize() != 0:
            time.sleep(0.1)

def get_remote_mapping(remotes):
    rmap = {}

    for remote in remotes:
        (stdout, _, _) = exec(remote, 'ip netns list', get_output=True)
        for line in stdout.split():
            if line.startswith('ns-'):
                rmap[line.strip()] = remote

    return rmap

# create a neighbor dict from a json network description
def convert_to_neighbors(network):
    neighbors = {}

    # create a structure we can use efficiently
    for node in network.get('nodes', []):
        neighbors.setdefault(str(node['id']), [])

    for link in network.get('links', []):
        source = str(link['source'])
        target = str(link['target'])
        neighbors.setdefault(source, []).append(target)
        neighbors.setdefault(target, []).append(source)

    return neighbors

def format_duration(time_ms):
    d, remainder = divmod(time_ms, 24 * 60 * 60 * 1000)
    h, remainder = divmod(remainder, 60 * 60 * 1000)
    m, remainder = divmod(remainder, 60 * 1000)
    s, remainder = divmod(remainder, 1000)
    ms = remainder

    if d > 0:
        if h > 0:
            return '{}.{}d'.format(int(d), int(h))
        return '{}d'.format(int(d))
    elif h > 0:
        if m > 0:
            return '{}.{}h'.format(int(h), int(m))
        return '{}h'.format(int(h))
    elif m > 0:
        if s > 0:
            return '{}.{}m'.format(int(m), int(s))
        return '{}m'.format(int(m))
    elif s > 0:
        if ms > 0:
            return '{}.{}s'.format(int(s), int(ms))
        return '{}s'.format(int(s))
    else:
        return '{}ms'.format(int(ms))
