#!/usr/bin/env python

"""
    Main module to orchestrate nodes
"""

import sys
import threading
import matplotlib.pyplot as plt
import matplotlib as mpl
import networkx as nx
from node import Node

class Drawer(threading.Thread):
    """
        Class to draw the network graph
    """

    def __init__(self, nodes):
        super().__init__()
        self.nodes = nodes
        self.graph = nx.DiGraph()
        self._generate_graph()
        self.nodes_pos = nx.shell_layout(self.graph)

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
            return 'green'
        if node.asked:
            return 'blue'
        return 'grey'

    def _generate_graph(self):
        """
            Generates the graph
        """
        self.graph.clear()
        for node in self.nodes:
            self.graph.add_node(node.name)
            if node.holder != 'self':
                self.graph.add_edge(node.name, node.holder)
        #when node.initialize_network() is not called,
        # a 'None' node will be in the graph (why ??)
        if None in self.graph:
            self.graph.remove_node(None)

    def _draw_graph(self):
        """
            Draws the graph
        """

        plt.clf()

        self._generate_graph()

        labels = {}
        for graph_node in self.graph.nodes():
            labels[graph_node] = graph_node

        colors = []
        for graph_node in self.graph.nodes():
            node = [node for node in self.nodes if node.name == graph_node][0]
            color = self._get_color(node)
            colors.append(color)

        nx.draw_networkx_nodes(self.graph, self.nodes_pos, node_color=colors)
        nx.draw_networkx_labels(self.graph, self.nodes_pos, labels, font_size=10, font_color='w')
        nx.draw_networkx_edges(self.graph, self.nodes_pos,
                               arrowstyle='->', arrowsize=10, width=2)

        axis = plt.gca()
        axis.set_axis_off()
        plt.pause(0.001)

    def run(self):
        while True:
            self._generate_graph()
            self._draw_graph()


def main():
    """
        Main code:
        - creates nodes
        - instanciates a 'drawer' to display a graph of the network
    """

    if len(sys.argv) < 3:
        sys.stderr.write("Usage: %s number_of_nodes node_to_initialize\n" % sys.argv[0])
        sys.exit(1)

    number_of_nodes = int(sys.argv[1])
    node_to_initialize = sys.argv[2]

    ### INIT NODES ###
    nodes = []
    for i in range(number_of_nodes):
        node_name = '%s' % i
        node = Node(node_name)
        node.consumer.start()
        nodes.append(node)

    nodes[0].neighbors = ['1', '2', '3']
    nodes[1].neighbors = ['0']
    nodes[2].neighbors = ['0']
    nodes[3].neighbors = ['0', '7', '4']
    nodes[4].neighbors = ['3', '5', '6']
    nodes[5].neighbors = ['4']
    nodes[6].neighbors = ['4']
    nodes[7].neighbors = ['3', '8', '9']
    nodes[8].neighbors = ['7']
    nodes[9].neighbors = ['7']

    Drawer(nodes).start()

    for node in nodes:
        if node.name == node_to_initialize:
            node.initialize_network()

    while True:
        try:
            asking_node = input('Which node will ask for the privilege?\n')
            for node in nodes:
                if node.name == asking_node:
                    node.ask_for_critical_section()
        except KeyboardInterrupt:
            sys.exit()

if __name__ == '__main__':
    main()
