import datetime
import subprocess
import threading
import queue
import atexit
import time
import sys
import re
import os


default_remotes = [{}] # local
terminals = {} # terminals (SSH/local)


def eprint(message):
    sys.stderr.write(f'{message}\n')

# get time in milliseconds
def millis():
    return int(1000 * time.time())

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
        self.output_lock = threading.Lock()
        self.output = {}
        self.start()

    def run(self):
        while True:
            try:
                # might raise Empty
                (ignore_error, get_output, command) = self.queue.get(block=True, timeout=1)

                p = create_process(self.remote, command)

                (std, err) = p.communicate()
                stdout = std.decode()
                errout = err.decode()

                if p.returncode != 0 and not ignore_error:
                    address = self.remote.get('address', 'local')
                    eprint(errout)
                    eprint(stdout)
                    eprint(f'Abort, command failed on {address}: {command}')
                    eprint('Network might be in an undefined state!')
                    exit(1)

                if get_output and self.queue.empty():
                    self.output_lock.acquire()
                    self.output[command] = (stdout, errout, p.returncode)
                    self.output_lock.release()
            except queue.Empty:
                # try again or finish loop
                if self.finish:
                    break
            except Exception as e:
                eprint(e)
                exit(1)

def exec(remote, command, get_output=False, ignore_error=False):
    i = id(remote)

    if not type(remote) is dict:
        print(f'Remote not a dict! {remote}')
        exit(1)

    if i not in terminals:
        terminals[i] = TerminalThread(remote)

    t = terminals[i]
    t.queue.put((ignore_error, get_output, command))

    while get_output:
        t.output_lock.acquire()
        result = t.output.pop(command, None)
        t.output_lock.release()
        if result:
            return result
        time.sleep(0.05)

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

# id independent of source/target direction
def link_id(source, target):
    if source > target:
        return f'{source}-{target}'
    else:
        return f'{target}-{source}'

def get_current_state(remotes):
    links = {}
    nodes = []
    rmap = {}

    node_re = re.compile(r'\d+: br-([^:]+)')
    link_re = re.compile(r'\d+: ve-([^@:]+).*(?<= master )br-([^ ]+)')

    for remote in remotes:
        stdout, stderr, rcode = exec(remote, f'ip netns exec "switch" ip a l || true', get_output=True)

        for line in stdout.splitlines():
            m = link_re.search(line)
            if m:
                ifname = m.group(1) # without ve-
                master = m.group(2) # without br-
                source = ifname[:len(master)]
                target = ifname[len(master) + 1:]

                lid = link_id(source, target)
                if lid not in links:
                    links[lid] = {'source': source, 'target': target}
            m = node_re.search(line)
            if m:
                ifname = m.group(1) # without br-
                nodes.append({'id': ifname})
                rmap[ifname] = remote

    return ({'nodes': nodes, 'links': list(links.values())}, rmap)

def get_remote_mapping(remotes):
    rmap = {}

    for remote in remotes:
        (stdout, _, _) = exec(remote, 'ip netns list', get_output=True)
        for line in stdout.split():
            if line.startswith('ns-'):
                rmap[line.strip()[3:]] = remote

    return rmap

# create a neighbor dict from a json network description
def convert_to_neighbors(*networks):
    neighbors = {}

    for network in networks:
        # create a structure we can use efficiently
        for node in network.get('nodes', []):
            neighbors.setdefault(str(node['id']), set())

        for link in network.get('links', []):
            source = str(link['source'])
            target = str(link['target'])
            neighbors.setdefault(source, set()).add(target)
            neighbors.setdefault(target, set()).add(source)

    ret = {}
    for key, value in neighbors.items():
        ret[key] = list(value)

    return ret

def check_access(remotes):
    # single empty remote with no address => local
    if len(remotes) == 1 and ('address' not in remotes[0]):
        if os.geteuid() == 0:
            # must be root
            return
        else:
            eprint('Local setup needs to run as root.')
            stop_all_terminals()
            exit(1)

    for remote in remotes:
        if 'address' in remote:
            # check if we can execute something
            exec(remote, 'true')
        else:
            eprint('Need external address for all remotes.')
            stop_all_terminals()
            exit(1)

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

def format_size(bytes):
    if bytes < 1000:
        return f'{bytes:.2f} B'
    elif bytes < 1000_000:
        return f'{bytes / 1000:.2f} K'
    elif bytes < 1000_000_000:
        return f'{bytes / 1000_000:.2f} M'
    else:
        return f'{bytes / 1000_000_000:.2f} G'
