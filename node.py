#!/usr/bin/env python3

from fifo import Fifo
import sys
import time
import threading
import pika

class Consumer(threading.Thread):

    def __init__(self, name, callback):
        super().__init__()
        self._name = name
        self._callback = callback
        self.set_up_connection()

    def set_up_connection(self):
        self._connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        channel = self._connection.channel()
        channel.exchange_declare(exchange='raymond', exchange_type='topic')
        channel.queue_declare(queue=self._name, exclusive=True)
        channel.queue_bind(exchange='raymond', queue=self._name, routing_key='%s.*' % self._name)
        channel.basic_consume(self._callback, queue=self._name, no_ack=True)
        self._channel = channel

    def run(self):
        self._channel.start_consuming()

class Publisher():

    def __init__(self, name):
        self._name = name
        self.set_up_connection()

    def set_up_connection(self):
        self._connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        channel = self._connection.channel()
        channel.exchange_declare(exchange='raymond', exchange_type='topic')
        self._channel = channel

    def send_request(self, target_node, request_type):
        routing_key = '%s.%s' % (target_node, request_type)
        self._channel.basic_publish(exchange='raymond', routing_key=routing_key, body="%s" % self._name)

class Node(threading.Thread):

    def __init__(self, name, neighbors=None):
        super().__init__()
        self.name = name
        self.holder = 'self'
        self.using = False
        self.request_q = Fifo([])
        self.asked = False
        self.neighbors = neighbors if neighbors else []
        self.consumer_thread = Consumer(self.name, self.treat_message)
        self.publisher = Publisher(self.name)

    def run(self):
        self.consumer_thread.start()

    def _assign_privilege(self):
        if self.holder == 'self' and not self.using and not self.request_q.empty():
            self.holder = self.request_q.get()
            self.asked = False
            if self.holder == 'self':
                self.using = True
                self._enter_critical_section()#Critical section
                self.exit_critical_section()
            else:
                self.publisher.send_request(self.holder, 'privilege')

    def _make_request(self):
        if self.holder != 'self' and not self.request_q.empty() and not self.asked:
            self.publisher.send_request(self.holder, 'request')
            self.asked = True

    def _assign_privilege_and_make_request(self):
        time.sleep(0.5)
        self._assign_privilege()
        self._make_request()

    def ask_for_critical_section(self):
        self.request_q.push('self')
        self._assign_privilege_and_make_request()

    def receive_request(self, sender):
        self.request_q.push(sender)
        self._assign_privilege_and_make_request()

    def receive_privilege(self, sender):
        self.holder = 'self'
        self._assign_privilege_and_make_request()

    def exit_critical_section(self):
        self.using = False
        self._assign_privilege_and_make_request()

    def _initialize_network(self, init_sender=None):
        neighbors = self.neighbors.copy()
        if init_sender:
            neighbors.remove(init_sender)
        for neighbor in neighbors:
            self.publisher.send_request(neighbor, 'initialize')


    def _enter_critical_section(self):
        time.sleep(2)

    def treat_message(self, ch, method, properties, body):
        message_type = method.routing_key.split('.')[1]
        sender = body.decode('UTF-8')
        # print("%s: Received %s from %s" % (self.name, message_type, sender))
        if message_type == 'request':
            self.receive_request(sender)
        if message_type == 'privilege':
            self.receive_privilege(sender)
        if message_type == 'initialize':
            self.holder = sender
            self._initialize_network(sender)

if __name__ == '__main__':

    if len(sys.argv) < 2:
        sys.stderr.write("Usage: %s node_name\n" % sys.argv[0])
        sys.exit(1)

    node_name = sys.argv[1]
    node = Node(node_name)

    node.start()

    #connection.close()