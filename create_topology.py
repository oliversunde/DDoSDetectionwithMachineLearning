
from mininet.net import Mininet
from mininet.node import Controller, OVSSwitch, RemoteController

from mininet.cli import CLI
from mininet.log import setLogLevel, info
import pydot

def visualize_topology(net, output_file='topology.png'):
    graph = pydot.Dot(graph_type='graph', rankdir='LR')

    for node in net.values():
        graph.add_node(pydot.Node(node.name, label=node.name, shape='circle'))

    for node1, node2 in net.links(sort=True):
        graph.add_edge(pydot.Edge(node1.name, node2.name))

    graph.write_png(output_file)

def create_topology():
    net = Mininet(controller=RemoteController, switch=OVSSwitch)

    info('*** Adding controller\n')
    net.addController('c0', controller=RemoteController, ip='127.0.0.1', port

    info('*** Adding hosts\n')
    hosts = []
    for i in range(1, 25):
        host = net.addHost(f'h{i}', ip=f'10.0.0.{i}')
        hosts.append(host)

    info('*** Adding switches\n')
    edge_switches = [net.addSwitch(f's{i}') for i in range(1, 9)]
    aggregation_switches = [net.addSwitch(f'a{i}') for i in range(1, 3)]
    core_switch = net.addSwitch('c1')

    info('*** Creating links\n')

    # Connect hosts to edge switches
    for i, host in enumerate(hosts):
        net.addLink(host, edge_switches[i % 8])

    # Connect edge switches to aggregation switches
    for i, edge_switch in enumerate(edge_switches):
        net.addLink(edge_switch, aggregation_switches[i % 2])

    # Connect aggregation switches to core switch
    for agg_switch in aggregation_switches:
        net.addLink(agg_switch, core_switch)

    info('*** Starting network\n')
    net.start()

    # Visualize the topology
    visualize_topology(net)

    info('*** Running CLI\n')
    CLI(net)

    info('*** Stopping network\n')
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    create_topology()
