from collections import deque

class Fifo(deque):

    def __init__(self, elements = None):
        super().__init__(elements)

    def head(self):
        return self[-1]

    def push(self, element):
        self.appendleft(element)

    def get(self):
        return self.pop()

    def empty(self):
        return len(self) == 0

