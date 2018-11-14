#!/usr/bin/env python

from node import Node
import matplotlib as mpl
import matplotlib.pyplot as plt
import networkx as nx
import pika
import subprocess
import sys
import threading
import time

NUMBER_OF_NODES = 10

plt.ion()

class Drawer(threading.Thread):

    def __init__(self, nodes):
        super().__init__()
        self.nodes = nodes
        self.graph = nx.DiGraph()

    def get_color(self, node):
        if node.holder == 'self':
            return 'green'
        elif node.asked:
            return 'blue'
        return 'grey'

    def _generate_graph(self):
        self.graph.clear()
        for node_name in self.nodes:
            node = self.nodes[node_name]
            self.graph.add_node(node_name)
            if node.holder != 'self':
                self.graph.add_edge(node.name, node.holder)

    def _draw_graph(self):

        plt.clf()

        self._generate_graph()

        labels = {}
        for node in self.graph.nodes():
            labels[node] = node

        colors = []
        for graph_node in self.graph.nodes():
            node = [ self.nodes[node_name] for node_name in self.nodes if node_name == graph_node ][0]
            color = self.get_color(node)
            colors.append(color)

        nx.draw_networkx_nodes(self.graph, self.nodes_pos, node_color=colors)
        nx.draw_networkx_labels(self.graph, self.nodes_pos, labels, font_size=10, font_color='w')
        nx.draw_networkx_edges(self.graph, self.nodes_pos, arrowstyle='->', arrowsize=10, edge_cmap=plt.cm.Blues, width=2)

        ax = plt.gca()
        ax.set_axis_off()
        plt.pause(0.001)

    def run(self):

        self._generate_graph()
        self.nodes_pos = nx.layout.shell_layout(self.graph)

        while True:
            self._generate_graph()
            self._draw_graph()


def main():

    if len(sys.argv) < 3:
        sys.stderr.write("Usage: %s number_of_nodes node_to_initialize\n" % sys.argv[0])
        sys.exit(1)

    number_of_nodes = int(sys.argv[1])
    node_to_initialize = sys.argv[2]

    ### INIT NODES ###
    nodes = {}
    for i in range(number_of_nodes):
        node_name = str(i)
        nodes[node_name] = Node(node_name)

    nodes['0'].neighbors = ['1', '2', '3']
    nodes['1'].neighbors = ['0']
    nodes['2'].neighbors = ['0']
    nodes['3'].neighbors = ['0', '7', '4']
    nodes['4'].neighbors = ['3', '5', '6']
    nodes['5'].neighbors = ['4']
    nodes['6'].neighbors = ['4']
    nodes['7'].neighbors = ['3', '8', '9']
    nodes['8'].neighbors = ['7']
    nodes['9'].neighbors = ['7']

    for node in nodes.values():
        node.start()

    Drawer(nodes).start()

    nodes[node_to_initialize]._initialize_network()

    while True:
        try:
            asking_node = input('Which node will ask for the privilege?\n')
            try:
                nodes[asking_node].ask_for_critical_section()
            except KeyError:
                print('No node with this name !\n')
        except KeyboardInterrupt:
            sys.exit()

if __name__ == '__main__':
    main()