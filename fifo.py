"""
    For a handy Fifo queue
"""

from collections import deque


class Fifo(deque):
    """
        Class to implement handy methods for a Fifo queue with deque
    """

    def __init__(self, elements=None):
        if elements is None:
            elements = []
        super(Fifo, self).__init__(elements)

    def head(self):
        """
            Returns first element in the queue
        """
        return self[-1]

    def push(self, element):
        """
            Adds an element in the queue
        """
        self.appendleft(element)

    def get(self):
        """
            Returns first element of the queue
        """
        return self.pop()

    def empty(self):
        """
            Returns whether the queue is empty
        """
        return len(self) == 0
