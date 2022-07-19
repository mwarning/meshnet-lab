#!/usr/bin/env python3

import os
import sys
import time
import glob
import copy
import math
import json
import copy

# for animation
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import collections as mc
from matplotlib.animation import FuncAnimation

sys.path.append('../../')
import software
import network
import topology
import mobility
import traffic
import ping
from shared import Remote
import shared


MAX_STATION_TO_SATELLITE_CONNECTIONS = 2
MAX_STATION_TO_SATELLITE_DISTANCE = 2_000_000
MAX_SATELLITE_TO_SATELLITE_CONNECTIONS = 8
MAX_SATELLITE_TO_SATELLITE_DISTANCE = 2_000_000

SPEEDUP = 100 # speedup simulation compared to realtime (100x makes an interesting animation)

unique_id_counter = 0

def getNewUniqueID():
    global unique_id_counter
    new_id = unique_id_counter
    unique_id_counter += 1
    return new_id

class Satellite:
    def __init__(self, height, azimuth, inclination,
                 offset_t=0, offset_azimuth=0):
        self.id = getNewUniqueID()
        self.name = str(self.id)
        self.plot = None # for animation
        self.height = height
        self.azimuth = np.radians(azimuth)  # 0-360°
        self.inclination = np.radians(inclination)  # 0-90°
        self.T = self.satellite_period(height)
        self.offset_azimuth = np.radians(offset_azimuth)
        self.offset_t = np.radians(offset_t)
        self.pos = [0, 0, 0]

    # get orbital period in seconds
    def satellite_period(self, h):
        G = 6.67430e-11  # gravitational constant
        M = 5.9722e24  # earth mass
        R = 6371000  # earth radius
        r = R + h
        v = np.sqrt(G * M / r)
        return 2 * np.pi * r / v

    def update_position(self, t):
        R = 6371000  # earth radius
        r = R + self.height
        z = self.offset_azimuth + self.azimuth
        a = self.inclination
        p = self.offset_t + 2 * np.pi * t / self.T
        self.pos[0] = r * (np.cos(a)*np.cos(z)*np.cos(p) - np.sin(z)*np.sin(p))
        self.pos[1] = r * (np.cos(a)*np.sin(z)*np.cos(p) + np.cos(z)*np.sin(p))
        self.pos[2] = r * np.sin(a)*np.cos(p)

# ground station
class Station():
    def __init__(self, name, lat, lon):
        R = 6371000  # earth radius
        self.id = getNewUniqueID()
        self.name = name
        self.height = R
        self.plot = None # for animation

        lat = np.radians(lat)
        lon = np.radians(lon)

        self.pos = [R * np.cos(lat) * np.cos(lon),
                    R * np.cos(lat) * np.sin(lon),
                    R * np.sin(lat)]

# get list of ground stations
def get_station_set1():
    return [
        Station("Paris", 48.864716, 2.349014),
        Station("Berlin", 52.52437, 13.41053),
        Station("New York", 40.7127837, -74.0059413),
        Station("Seoul", 37.532600, 127.024612),
        Station("New Dehli", 28.679079, 77.069710),
        Station("Rio de Janeiro", -22.908333, -43.196388),
    ]

# get list of satellites
def get_satellite_set1():
    NUM_SATELLITES = 30
    satellites = []

    for i in range(0, NUM_SATELLITES):
        satellites.append(Satellite(550000, 0, 53, i * 360 / NUM_SATELLITES, 0))

    for i in range(0, NUM_SATELLITES):
        satellites.append(Satellite(560000, 0, 53, i * 360 / NUM_SATELLITES, 200))

    for i in range(0, NUM_SATELLITES):
        satellites.append(Satellite(570000, 0, 53, i * 360 / NUM_SATELLITES, 240))

    return satellites

# squared distance
def distance2(pos1, pos2):
    return (pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2 + (pos1[2] - pos2[2]) ** 2

def distance(pos1, pos2):
    return np.sqrt(distance2(pos1, pos2))

def get_connections(stations, satellites):
    connections = []

    # connect satellites
    for s1 in satellites:
        found = []
        for s2 in satellites:
            d2 = distance2(s1.pos, s2.pos)
            if d2 > 0 and d2 <= (MAX_SATELLITE_TO_SATELLITE_DISTANCE ** 2):
                found.append((s1, s2, d2))
        found.sort(key=lambda s: s[2])
        connections.extend(found[:MAX_SATELLITE_TO_SATELLITE_CONNECTIONS])

    # connect stations and satellites
    for s1 in stations:
        found = []
        for s2 in satellites:
            d2 = distance2(s1.pos, s2.pos)
            if d2 > 0 and d2 <= (MAX_STATION_TO_SATELLITE_DISTANCE ** 2):
                found.append((s1, s2, d2))
        found.sort(key=lambda s: s[2])
        connections.extend(found[:MAX_STATION_TO_SATELLITE_CONNECTIONS])

    return connections


# for creating a visual animation
def start_animation(satellites, stations):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    ax.set_xlim3d([-7000000.0, 7000000.0])
    ax.set_xlabel('X')

    ax.set_ylim3d([-7000000.0, 7000000.0])
    ax.set_ylabel('Y')

    ax.set_zlim3d([-7000000, 7000000.0])
    ax.set_zlabel('Z')

    # height => plot object for satellites/stations
    plots = {}
    def getPlot(height):
        h = int(height)
        if h not in plots:
            plots[h] = ax.scatter3D([], [], [])
        return plots[h]

    def getColor(s1, s2, d):
        if isinstance(s1, Station) or isinstance(s2, Station):
            r = d / MAX_STATION_TO_SATELLITE_DISTANCE
            return (0.6 * r, 1.0 - r , 0.0)
        else:
            r = d / MAX_STATION_TO_SATELLITE_DISTANCE
            return (0.6 * r, 1.0 - r , 0.0)

    for s in stations:
        s.plot = getPlot(s.height)

    for s in satellites:
        s.plot = getPlot(s.height)

    # ground stations do not move => print labels once here
    for s in stations:
        # add labels to ground stations
        ax.text(s.pos[0], s.pos[1], s.pos[2], s.name, size=10, zorder=1, color='k')

    started = time.time() # seconds until epoch

    lines = []
    def update(i):
        sim_time = SPEEDUP * (time.time() - started)
        plt.title(f'Time: {int((sim_time/(60*60))%24):02d}h:{int((sim_time/60)%60):02d}m:{int(sim_time%60):02d}s (x{SPEEDUP})')

        # remove previous connections/links
        for line in lines:
            line.remove()
        lines.clear()

        # calculate satellite positions (stations do not change)
        for s in satellites:
            s.update_position(sim_time)

        for h, plot in plots.items():
            plot._offsets3d = ([], [], [])

        for s in stations:
            s.plot._offsets3d[0].append(s.pos[0])
            s.plot._offsets3d[1].append(s.pos[1])
            s.plot._offsets3d[2].append(s.pos[2])

        for s in satellites:
            s.plot._offsets3d[0].append(s.pos[0])
            s.plot._offsets3d[1].append(s.pos[1])
            s.plot._offsets3d[2].append(s.pos[2])

        connections = get_connections(stations, satellites)
        for c in connections:
            p1 = c[0].pos
            p2 = c[1].pos
            d = np.sqrt(c[2])

            line, = ax.plot([p1[0], p2[0]], [p1[1], p2[1]], [p1[2], p2[2]], linewidth=1, color=getColor(c[0], c[1], d))
            lines.append(line)

    fig.tight_layout()
    ani = FuncAnimation(fig, update, frames=10)

    #ani.save('animation.gif', writer='imagemagick', fps=20)

    plt.show()
    exit(0)


# JSON representation of the current state
# name, x, y, z, distance are optional
def get_state(stations, satellites, connections):
    links = []
    nodes = []

    # add satellites and connect them
    for s in satellites:
        nodes.append({"id": s.id, "x": s.pos[0], "y": s.pos[1], "z": s.pos[2]})

    for s in stations:
        nodes.append({"id": s.id, "name": s.name, "x": s.pos[0], "y": s.pos[1], "z": s.pos[2]})

    for c in connections:
        links.append({"source": c[0].id, "target": c[1].id, "distance": np.sqrt(c[2])})

    return {"nodes": nodes, "links": links}

satellites = get_satellite_set1()
stations = get_station_set1()

# uncomment for animation
#start_animation(satellites, stations)

remotes= [Remote()]

shared.check_access(remotes)
software.clear(remotes)
network.clear(remotes)

prefix = os.environ.get('PREFIX', '')

def print_stations():
    print('station names:')
    for s in stations:
        print(f'{s.id} => {s.name}')

# calculate median
# input: [([...], [...]), ([...], [...]), ...]
# output: [(...), (...)]
def merge_results(results):
    ret = copy.copy(results[0])
    for result in results[1:]:
        for i, value in enumerate(result[1]):
            ret[1][i] += value

    for i, value in enumerate(ret[1]):
        ret[1][i] /= len(ret[0])

    return ret

def run(protocol, csvfile):
    # informal, data does not change
    print_stations()

    # pick 20 random paths between ground stations
    paths = ping.get_random_paths(get_state(stations, [], []), 20)

    # create network and start routing software
    state = get_state(stations, satellites, [])
    network.apply(state, remotes=remotes)

    DURATION_SIMTIME_SEC = 2*60*60 # 2 hours in simulation time for each round
    STEP_SIMTIME_SEC = 5*60 # update simulation and measure every 5 minutes

    for speedup in range(4, 36, 2):
        shared.seed_random(42)
        software.start(protocol)

        ping_results = []
        traffic_begin = traffic.traffic()
        test_beg_ms = shared.millis()

        step_realtime_sec = int(STEP_SIMTIME_SEC / speedup)
        for sim_time_sec in range(0, DURATION_SIMTIME_SEC, STEP_SIMTIME_SEC):
            wait_beg_ms = shared.millis()
            real_time_sec = (wait_beg_ms - test_beg_ms) / 1000

            print(f'{protocol}: speedup: {speedup}x, sim time {int(sim_time_sec)}s, real time {int(real_time_sec)}s')

            # update node positions
            for s in satellites:
                s.update_position(sim_time_sec)

            # update network
            connections = get_connections(stations, satellites)
            state = get_state(stations, satellites, connections)

            network.apply(state=state, remotes=remotes)

            # waits until time is up (errors if time is already up!)
            shared.wait(wait_beg_ms, step_realtime_sec - 2)

            ping_result = ping.ping(paths=paths, duration_ms=2000, verbosity='verbose', remotes=remotes)
            ping_results.append(ping_result.getData())

            #realtime_sec = (shared.millis() - test_beg_ms) / 1000
            #traffic_end = traffic.traffic()

            # add data to csv file
            #extra = (['x', 'speedup', 'station_count', 'satellite_count', 'realtime_sec', 'simtime_sec'],
            #    [f'{speedup}_{realtime_sec}', speedup, len(stations), len(satellites), realtime_sec, sim_time_sec])
            #shared.csv_update(csvfile, '\t', extra, (traffic_end - traffic_begin).getData(), ping_result.getData())

        sim_time_sec = DURATION_SIMTIME_SEC
        realtime_sec = (shared.millis() - test_beg_ms) / 1000
        traffic_end = traffic.traffic()
        ping_result = merge_results(ping_results)

        # add data to csv file
        extra = (['speedup', 'station_count', 'satellite_count', 'realtime_sec', 'simtime_sec'],
            [speedup, len(stations), len(satellites), sim_time_sec, realtime_sec])
        shared.csv_update(csvfile, '\t', extra, (traffic_end - traffic_begin).getData(), ping_result)

        software.clear(remotes)

    network.clear(remotes)

for protocol in ['batman-adv', 'babel', 'batman-adv', 'bmx6', 'bmx7', 'cjdns', 'olsr1', 'olsr2', 'yggdrasil']:
    with open(f"{prefix}satellites2-{protocol}.csv", 'w+') as csvfile:
        run(protocol, csvfile)

shared.stop_all_terminals()
