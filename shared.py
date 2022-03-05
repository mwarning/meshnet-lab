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
        exit(1)

def load_json(path):
    with open(path) as file:
        return json.load(file)
    return None

def seed_random(value):
    random.seed(value)

def sleep(seconds):
    time.sleep(seconds)

def wait(beg_ms, until_sec):
    now_ms = millis()

    # wait until time is over
    if (now_ms - beg_ms) < (until_sec * 1000):
        time.sleep(((until_sec * 1000) - (now_ms - beg_ms)) / 1000.0)
    else:
        eprint('Wait timeout already passed by {:.2f}sec'.format(((now_ms - beg_ms) - (until_sec * 1000)) / 1000))
        stop_all_terminals()
        exit(1)

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

def json_count(path):
    obj = path

    if isinstance(path, str):
        with open(path) as file:
            obj = json.load(file)

    links = obj.get('links', [])
    nodes = {}
    for link in links:
        nodes[link['source']] = 0;
        nodes[link['target']] = 0;
    links = obj.get('links', [])

    return (len(nodes), len(links))

# add titles and values to a CSV file
def csv_update(file, delimiter, *args):
    titles = list()
    values = list()

    for arg in args:
        titles += arg[0]
        values += arg[1]

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

    for remote in remotes:
        stdout = exec(remote, 'uptime', get_output=True)[0]
        t = stdout.split('load average:')[1].split(',')
        load1 += float(t[0])
        load5 += float(t[1])
        load15 += float(t[2])

    titles = ['load1', 'load5', 'load15']
    values = [load1 / len(remotes), load5 / len(remotes), load15 / len(remotes)]

    return (titles, values)


def create_process(remote, command, add_quotes=True):
    if remote.address:
        if add_quotes:
            command = command.replace('\'', '\\\'') # need to escape
            command = f'\'{command}\''

        if remote.ifile:
            command = f'ssh -p {remote.port} -i {remote.ifile} root@{remote.address} {command}'
        else:
            command = f'ssh -p {remote.port} root@{remote.address} {command}'
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
                (ignore_error, get_output, add_quotes, command) = self.queue.get(block=True, timeout=1)

                p = create_process(self.remote, command, add_quotes)

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

def exec(remote, command, get_output=False, ignore_error=False, add_quotes=True):
    if remote not in terminals:
        terminals[remote] = TerminalThread(remote)

    t = terminals[remote]
    t.queue.put((ignore_error, get_output, add_quotes, command))

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
    if len(remotes) == 1 and remotes[0].address is None:
        if os.geteuid() == 0:
            # we are root
            return
        else:
            eprint('Need to run as root for local execution.')
            stop_all_terminals()
            exit(1)

    for remote in remotes:
        if remote.address is None:
            eprint('Need external address for all remotes.')
            stop_all_terminals()
            exit(1)

        # check if we can execute something
        (stdout, stderr, rcode) = exec(remote, 'true', get_output=True, ignore_error=True)
        if rcode != 0:
            eprint(stdout)
            eprint(stderr)
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
