#!/usr/bin/env python3
import argparse
import json
from graphviz import Graph

def draw(file):
    dot = Graph()
    f = json.load(file)
    
    for node in f["nodes"]:
        dot.node(str(node["id"]))

    for link in f["links"]:
        dot.edge(str(link["source"]), str(link["target"]))

    print(dot.source)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("graph_file", type=argparse.FileType('r'), help="Path to the created graph json file")
    args = parser.parse_args()
    draw(args.graph_file)
