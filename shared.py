import datetime
import subprocess
import threading
import random
import queue
import atexit
import json
import time
import sys
import re
import os


class Remote:
    def __init__(self, address=None, port=None, identity_file=None):
        self.address = address
        self.port = port or 22
        self.ifile = identity_file

    def __hash__(self):
        return hash((self.address, self.port, self.ifile))

    def __eq__(self, other):
        return (isinstance(other, type(self))
            and self.address == other.address
            and self.port == other.port
            and self.ifile == other.ifile
        )

    def from_json(obj):
        return Remote(obj.get("address"), obj.get("port"), obj.get("identity_file"))

default_remotes = [Remote()] # local
terminals = {} # terminals (SSH/local)

def eprint(message):
    sys.stderr.write(f'{message}\n')

# get time in milliseconds
def millis():
    return int(1000 * time.time())

def check_access(remotes):
    shared.check_access(remotes)

def root():
    if os.geteuid() != 0:
        eprint('Need to run as root.')
        stop_all_terminals()
        exit(1)

def load_json(path):
    with open(path) as file:
        return json.load(file)
    raise ValueError(f'File not found: {path}')

def seed_random(value):
    random.seed(value)

def sleep(seconds):
    time.sleep(seconds)

def wait(beg_ms, until_sec):
    now_ms = millis()

    # wait until time is over
    if (now_ms - beg_ms) < (until_sec * 1000):
        time.sleep(((until_sec * 1000) - (now_ms - beg_ms)) / 1000.0)
        return True
    else:
        eprint('Wait timeout already passed by {:.2f}sec'.format(((now_ms - beg_ms) - (until_sec * 1000)) / 1000))
        return False

def _get_clusters_sets(neighbors):
    visited = {}

    for node in neighbors:
        visited[node] = False

    def dfs(node, cluster):
        visited[node] = True
        cluster.add(node)
        for neighbor in neighbors[node]:
            if not visited[neighbor]:
                dfs(neighbor, cluster)

    clusters = []
    for node in visited:
        if not visited[node]:
            cluster = set()
            dfs(node, cluster)
            clusters.append(cluster)

    sorted(clusters, key=lambda cluster: len(cluster))
    return clusters

'''
Add links to network to make sure
it is fully connected.
'''
def make_connected(network):
    neighbors = convert_to_neighbors(network)
    clusters = _get_clusters_sets(neighbors)

    def get_unique_id(neighbors, i = 0):
        if f'ic-{i}' not in neighbors:
             return f'ic-{i}'
        else:
            return get_unique_id(neighbors, i + 1)

    def get_center_node(neighbors, cluster):
        max_neighbors = 0
        center_node = None
        for sid, neighs in neighbors.items():
            if sid in cluster and len(neighs) >= max_neighbors:
                max_neighbors = len(neighs)
                center_node = sid
        return center_node

    if len(clusters) > 1:
        central = get_unique_id(neighbors)

        # connect all clusters via central node
        for cluster in clusters:
            center = get_center_node(neighbors, cluster)
            network['links'].append({'source': central, 'target': center, 'type': 'vpn'})

# return number of nodes and links
def json_count(path):
    obj = path

    if isinstance(path, str):
        with open(path) as file:
            obj = json.load(file)

    links = set()
    nodes = set()

    for link in obj.get('links', []):
        source = str(link['source'])
        target = str(link['target'])
        nodes.add(source)
        nodes.add(target)
        links.add(link_id(source, target))

    for node in obj.get('nodes', []):
        nodes.add(str(node['id']))

    return (len(nodes), len(links))

# add titles and values to a CSV file
def csv_update(file, delimiter, *args):
    titles = list()
    values = list()

    for arg in args:
        if arg:
            titles.append(arg[0])
            values.append(arg[1])

    # convert elements to str
    for i in range(0, len(titles)):
        titles[i] = str(titles[i])

    # convert elements to str
    for i in range(0, len(values)):
        values[i] = str(values[i])

    if file.tell() == 0:
        file.write(delimiter.join(titles) + '\n')

    file.write(delimiter.join(values) + '\n')

def sysload(remotes=default_remotes):
    load1 = 0
    load5 = 0
    load15 = 0
    load_lock = threading.Lock()

    def collectResults(returncode, stdout, errout):
        t = stdout.split('load average:')[1].split(',')
        load_lock.acquire()
        nonlocal load1
        nonlocal load5
        nonlocal load15
        load1 += float(t[0])
        load5 += float(t[1])
        load15 += float(t[2])
        load_lock.release()

    for remote in remotes:
        tid = get_thread_id()
        exec(tid, remote, 'uptime', onResultCallBack=collectResults)

    wait_for_completion()

    titles = ['load1', 'load5', 'load15']
    values = [load1 / len(remotes), load5 / len(remotes), load15 / len(remotes)]

    return (titles, values)


def create_process(remote, command, add_quotes=False):
    # remote terminal
    if remote.address:
        if add_quotes:
            # need to escape
            command = command.replace('\'', '\\\'')
            command = f'\'{command}\''

        if remote.ifile:
            command = f'ssh -p {remote.port} -i {remote.ifile} root@{remote.address} {command}'
        else:
            command = f'ssh -p {remote.port} root@{remote.address} {command}'

    return subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

'''
Execute a command via SSH or local. All tasks in a
TerminalThread are executed in sequentional order.
'''
class TerminalThread(threading.Thread):
    def __init__(self, num, remote):
        super(TerminalThread, self).__init__()
        self.num = num
        self.remote = remote
        self.finish = False
        self.tasks = queue.Queue()
        self.start()

    def run(self):
        while True:
            try:
                # might raise Empty
                (ignore_error, command, onResultCallBack) = self.tasks.get(block=True, timeout=0.2)

                p = create_process(self.remote, command)

                (std, err) = p.communicate()
                stdout = std.decode()
                errout = err.decode()

                if p.returncode != 0 and not ignore_error:
                    label = self.remote.address or 'local'
                    eprint(stdout)
                    eprint(errout)
                    eprint(f'Abort, command failed on {label}: {command}')
                    eprint('Network might be in an undefined state!')
                    exit(1)

                if onResultCallBack:
                    onResultCallBack(p.returncode, stdout, errout)

                self.tasks.task_done()
            except queue.Empty:
                # try again or finish loop
                if self.finish:
                    break
            except Exception as e:
                eprint(e)
                exit(1)

class TerminalGroup():
    def __init__(self):
        self.terminals = {}
        self.cpu_count = os.cpu_count()
        self.cpu_counter = 0

    def addTask(self, tid, remote, command, ignore_error=False, onResultCallBack=None):
        idx = abs(tid) % self.cpu_count
        terminal = self.terminals.get(idx, None)
        if not terminal:
            # create another terminal
            terminal = TerminalThread(idx, remote)
            self.terminals[idx] = terminal

        terminal.tasks.put((ignore_error, command, onResultCallBack))
        return terminal

    def stopAllTerminals(self):
        for terminal in self.terminals.values():
            terminal.finish = True
        for terminal in self.terminals.values():
            terminal.join()

    def waitForCompletion(self):
        for terminal in self.terminals.values():
            terminal.tasks.join()

globalTerminalGroup = TerminalGroup()

def get_thread_id():
    globalTerminalGroup.cpu_counter += 1
    return globalTerminalGroup.cpu_counter

def exec(tid, remote, command, get_output=False, ignore_error=False, onResultCallBack=None):
    if get_output:
        result = None
        def onResult(rc, stdout, stderr):
            nonlocal result
            result = (stdout, stderr, rc)

        if onResultCallBack is not None:
            eprint('onResultCallBack not supported for get_output=True.')
            stop_all_terminals()
            exit(1)

        globalTerminalGroup.addTask(tid, remote, command, ignore_error, onResult)

        while result is None:
            time.sleep(0.01)
        return result
    else:
        globalTerminalGroup.addTask(tid, remote, command, ignore_error, onResultCallBack)

'''
The open terminal threads block our
program to exit if not finished
'''
def stop_all_terminals():
    globalTerminalGroup.stopAllTerminals()

def wait_for_completion():
    globalTerminalGroup.waitForCompletion()

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
        tid = get_thread_id()
        stdout, stderr, rcode = exec(tid, remote, f'ip netns exec "switch" ip a l || true', get_output=True)

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
        tid = get_thread_id()
        (stdout, _, _) = exec(tid, remote, 'ip netns list', get_output=True)
        for line in stdout.split():
            if line.startswith('ns-'):
                rmap[line.strip()[3:]] = remote

    return rmap

def get_all_nodes(network):
    return list(convert_to_neighbors(network).keys())

# create a neighbor dict from a json network description
# {node => [node..]}
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
    if len(remotes) == 1 and remotes[0].address is None:
        if os.geteuid() == 0:
            # we are root
            return
        else:
            eprint('Need to run as root for local execution.')
            stop_all_terminals()
            exit(1)

    for remote in remotes:
        tid = get_thread_id()

        if remote.address is None:
            eprint('Need external address for all remotes.')
            stop_all_terminals()
            exit(1)

        # check if we can execute something
        (stdout, stderr, rcode) = exec(tid, remote, 'true', get_output=True, ignore_error=True)
        if rcode != 0:
            eprint(stdout)
            eprint(stderr)
            stop_all_terminals()
            exit(1)
    wait_for_completion()

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
