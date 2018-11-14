#!/usr/bin/env python3

"""
    Implements a node
"""

import sys
import threading
import time
import pika
from fifo import Fifo

class Consumer(threading.Thread):
    """
        RabbitMQ consumer
    """

    def __init__(self, node_name, callback):
        super(Consumer, self).__init__()
        self._node_name = node_name
        self._callback = callback
        self.set_up_connection()

    def set_up_connection(self):
        """
            Sets the RabbitMQ connection
            Declares the queue with name 'node_name'
            Routing key for the queue is node_name.*
        """
        self._connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        channel = self._connection.channel()
        channel.exchange_declare(exchange='raymond', exchange_type='topic')
        channel.queue_declare(queue=self._node_name, exclusive=True)
        channel.queue_bind(exchange='raymond',
                           queue=self._node_name, routing_key='%s.*' % self._node_name)
        channel.basic_consume(self._callback, queue=self._node_name, no_ack=True)
        self._channel = channel

    def run(self):
        self._channel.start_consuming()

class Publisher:
    """
        RabbitMQ publisher
    """

    def __init__(self, node_name):
        self._node_name = node_name
        self.set_up_connection()

    def set_up_connection(self):
        """
            Sets the RabbitMQ connection
        """
        self._connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        channel = self._connection.channel()
        channel.exchange_declare(exchange='raymond', exchange_type='topic')
        self._channel = channel

    def send_request(self, target_node, request_type):
        """
            Sends message to RabbitMQ exchange
        """
        routing_key = '%s.%s' % (target_node, request_type)
        self._channel.basic_publish(exchange='raymond',
                                    routing_key=routing_key, body="%s" % self._node_name)

class Node(threading.Thread):
    """
        Node in the sense of Raymond's algorithm
        Implements the magical algorithm
    """

    def __init__(self, name, neighbors=None):
        super(Node, self).__init__()
        self.name = name
        self.holder = 'self'
        self.using = False
        self._request_q = Fifo()
        self.asked = False
        self.neighbors = neighbors if neighbors else []
        self.consumer_thread = Consumer(self.name, self._treat_message)
        self.publisher = Publisher(self.name)

    def run(self):
        self.consumer_thread.start()

    def _assign_privilege(self):
        """
            Implementation of ASSIGN_PRIVILEGE from Raymond's algorithm
        """
        if self.holder == 'self' and not self.using and not self._request_q.empty():
            self.holder = self._request_q.get()
            self.asked = False
            if self.holder == 'self':
                self.using = True
                self._enter_critical_section()
                self._exit_critical_section()
            else:
                self.publisher.send_request(self.holder, 'privilege')

    def _make_request(self):
        """
            Implementation of MAKE_REQUEST from Raymond's algorithm
        """
        if self.holder != 'self' and not self._request_q.empty() and not self.asked:
            self.publisher.send_request(self.holder, 'request')
            self.asked = True

    def _assign_privilege_and_make_request(self):
        """
            Calls assign_privilege and make_request
            sleep(x) allows to display what is happening
        """
        time.sleep(0.5)
        self._assign_privilege()
        self._make_request()

    def ask_for_critical_section(self):
        """
            When the node wants to enter the critical section
        """
        self._request_q.push('self')
        self._assign_privilege_and_make_request()

    def _receive_request(self, sender):
        """
            When the node receives a request from another
        """
        self._request_q.push(sender)
        self._assign_privilege_and_make_request()

    def _receive_privilege(self):
        """
            When the node receives the privilege from another
        """
        self.holder = 'self'
        self._assign_privilege_and_make_request()

    def _enter_critical_section(self):
        """
            Does stuff to simulate critical section
        """
        time.sleep(2)

    def _exit_critical_section(self):
        """
            When the node exits the critical section
        """
        self.using = False
        self._assign_privilege_and_make_request()

    def _treat_message(self, ch, method, properties, body):
        """
            Callback for the RabbitMQ consumer
            Messages are sent with 'node_name.type' routing keys and 'sender' as body
        """
        message_type = method.routing_key.split('.')[1]
        sender = body.decode('UTF-8')
        if message_type == 'request':
            self._receive_request(sender)
        if message_type == 'privilege':
            self._receive_privilege()
        if message_type == 'initialize':
            self.holder = sender
            self.initialize_network(sender)

    def initialize_network(self, init_sender=None):
        """
            When initializing, send initialize messages
            to neighbors BUT the one which sent it to the node (if it exists)
        """
        neighbors = self.neighbors.copy()
        if init_sender:
            neighbors.remove(init_sender)
        for neighbor in neighbors:
            self.publisher.send_request(neighbor, 'initialize')


if __name__ == '__main__':

    if len(sys.argv) < 2:
        sys.stderr.write("Usage: %s node_name\n" % sys.argv[0])
        sys.exit(1)

    NODE_NAME = sys.argv[1]
    NODE = Node(NODE_NAME)
    NODE.start()

    #connection.close()
