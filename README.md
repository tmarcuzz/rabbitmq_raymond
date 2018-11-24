# rabbitmq_raymond
Python implementation of Raymond's algorithm with RabbitMQ for a school project

## Usage

```bash
python main.py number_of_nodes
```

Then you can type three commands:
- to make nodes ask for critical section:
```
ask node1 node2 ... noden
```
- to kill nodes:
```
kill node1 node2 ... noden
```
- to quit:
```
exit
```

You can type `random` instead of `node`. This will create a thread that will randomly kill a node or make it ask for the critical section.

Example:
```
ask node1 random random
```