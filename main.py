#!/usr/bin/env python

"""
    Main module to orchestrate nodes
"""

from itertools import chain
import os
import sys
import threading
import matplotlib.pyplot as plt
import matplotlib as mpl
import networkx as nx
import random
from node import Node

mpl.use("TkAgg")

class CommandRunner(threading.Thread):
    def __init__(self, cmd, nodes, target):
        super().__init__()
        self.nodes = nodes
        self.target = target
        self.cmd = cmd

    def run(self):
        self.cmd(self.nodes, self.target)

class Controller(threading.Thread):
    """
        Class to listen to user input
    """

    def __init__(self, nodes):
        super().__init__()
        self.nodes = nodes

    def run(self):
        while True:
            cmd_line = input('>>> ')
            cmd_line_args = cmd_line.split(' ')
            cmd = cmd_line_args[0]
            if cmd == 'exit':
                print('exiting...')
                os._exit(0)
            if cmd == 'init':
                if len(cmd_line_args) != 2:
                    print('usage: init target_node')
                    continue
                target_node = cmd_line_args[1]
                CommandRunner(initialize_network, self.nodes, target_node).start()
            elif cmd == 'ask':
                if len(cmd_line_args) < 2:
                    print('usage: init [target_nodes]')
                    continue
                target_nodes = cmd_line_args[1:]
                for target_node in target_nodes:
                    CommandRunner(ask_for_critical_section, self.nodes, target_node).start()
            elif cmd == 'kill':
                if len(cmd_line_args) < 2:
                    print('usage: kill [target_nodes]')
                    continue
                target_nodes = cmd_line_args[1:]
                for target_node in target_nodes:
                    CommandRunner(kill, self.nodes, target_node).start()

class Drawer:
    """
        Class to draw the network graph.split(',').split(',')
    """

    def __init__(self, graph):
        self.graph = graph
        # self._generate_graph()
        self.nodes_pos = nx.spring_layout(self.graph)

        #set interactive mode on
        plt.ion()
        #disable toolbar
        mpl.rcParams['toolbar'] = 'None'

    def _get_color(self, node):
        """
            Gets the color corresponding to the node
            holder -> green
            asked -> blue
            other -> grey
        """
        if node.holder == 'self':
            return '#42c968'
        if node.asked:
            return "#4bdbdd"#'#5f7ecc'
        return 'w'

    def generate_graph(self):
        """
            Generates the graph
        """
        edges_to_delete = [edge for edge in self.graph.edges]
        for edge in edges_to_delete:
            self.graph.remove_edge(edge[0], edge[1])

        nodes = [self.graph.nodes[graph_node]['node'] for graph_node in self.graph.nodes()]
        for node in nodes:
            if node.holder != 'self' and node.holder is not None:
                self.graph.add_edge(int(node.name), int(node.holder))
        #when node.initialize_network() is not called,
        # a 'None' node will be in the graph (why ??)
        if None in self.graph:
            self.graph.remove_node(None)

    def draw_graph(self):
        """
            Draws the graph
        """

        plt.clf()

        labels = {}
        for graph_node in self.graph.nodes():
            labels[graph_node] = graph_node

        colors = []
        edge_colors = []
        line_widths = []
        for graph_node in self.graph.nodes():
            color = self._get_color(self.graph.node[graph_node]['node'])
            colors.append(color)
            if 'self' in self.graph.node[graph_node]['node']._request_q:
                edge_colors.append('black')
                line_widths.append(2.5)
            else:
                edge_colors.append('black')
                line_widths.append(1)

        nx.draw_networkx_nodes(self.graph, self.nodes_pos, node_color=colors, edgecolors=edge_colors, linewidths=line_widths)
        nx.draw_networkx_labels(self.graph, self.nodes_pos, labels, font_size=10, font_color='black')
        nx.draw_networkx_edges(self.graph, self.nodes_pos,
                               arrowstyle='->', arrowsize=10)

        axis = plt.gca()
        axis.set_axis_off()
        plt.pause(0.1)

def initialize_network(nodes, init_node):
    """
        Initialize the nodes
    """
    for node in nodes:
        if node.name == init_node:
            node.initialize_network()

def ask_for_critical_section(nodes, asking_node):
    """
        Make the asking_nodes ask for the critical section
    """
    for node in nodes:
        if node.name == asking_node:
            node.ask_for_critical_section()

def kill(nodes, node_to_kill):
    """
        Kill the node
    """
    for node in nodes:
        if node.name == node_to_kill:
            node.kill()


def main():
    """
        Main code:
        - creates nodes
        - instanciates a 'drawer' to display a graph of the network
    """

    if len(sys.argv) < 2:
        sys.stderr.write("Usage: %s number_of_nodes\n" % sys.argv[0])
        sys.exit(1)

    number_of_nodes = int(sys.argv[1])

    ### INIT NODES with a graph
    graph = nx.gn_graph(number_of_nodes)

    nodes = []
    for i in range(number_of_nodes):
        node_name = '%s' % i
        neighbors = [str(node) for node in chain(graph.predecessors(i), graph.successors(i))]
        node = Node(node_name, neighbors)
        node.consumer.start()
        nodes.append(node)
    
    initialize_network(nodes, str(random.randint(0, number_of_nodes-1)))

    graph_attributes = {}
    for i in range(len(nodes)):
        graph_attributes[i] = {
            'node': nodes[i],
            'label': nodes[i].name
        }

    nx.set_node_attributes(graph, graph_attributes)

    drawer = Drawer(graph)
    Controller(nodes).start()
    while True:
        drawer.generate_graph()
        drawer.draw_graph()


if __name__ == '__main__':
    main()
