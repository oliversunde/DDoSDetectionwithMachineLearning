from mininet.topo import Topo
from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel, info
from mininet.node import RemoteController
from mininet.cli import CLI


def get_honeypot_port(net, switch, honeypot):
    return net.linksBetween(net.getNodeByName(switch), net.getNodeByName(honeypot))[0].intf1


class CustomRemoteController(RemoteController):
    def __init__(self, name, ip='127.0.0.1', port=6633, honeypot_port=None, **kwargs):
        super(CustomRemoteController, self).__init__(
            name, ip=ip, port=port, **kwargs)
        self.honeypot_port = honeypot_port

    def start(self):
        super(CustomRemoteController, self).start()
        if self.honeypot_port:
            os.environ["HONEYPOT_PORT"] = str(self.honeypot_port)
        # Pass honeypot_port to your Ryu application
        # ...


class CustomTopology(Topo):
    def build(self):
        # Create three layer-1 switches
        self.layer1_switches = []
        for i in range(1, 4):
            layer1_switch = self.addSwitch('s1{}'.format(i))
            self.layer1_switches.append(layer1_switch)

        # Create six layer-2 switches and connect them to layer-1 switches
        layer2_switches = []
        for i in range(1, 7):
            layer2_switch = self.addSwitch('s2{}'.format(i))
            layer2_switches.append(layer2_switch)
            self.addLink(layer2_switch, self.layer1_switches[(i - 1) // 2])

        # Create 24 hosts and connect them to layer-2 switches
        for i in range(1, 25):
            host = self.addHost('h{}'.format(i))
            self.addLink(host, layer2_switches[(i - 1) // 4])

        self.honeypot = self.addHost('honeypot')
        self.addLink(self.honeypot, self.layer1_switches[0])


def run_custom_topology(controller_ip, traffic_func=None):
    topo = CustomTopology()
    net = Mininet(topo=topo, controller=lambda name: CustomRemoteController(
        name, ip=controller_ip))
    honeypot_port = get_honeypot_port(
        net, topo.layer1_switches[0], topo.honeypot)
    net.controller.honeypot_port = honeypot_port
    net.start()

    dumpNodeConnections(net.hosts)
    if traffic_func:
        traffic_func(net)
    info('*** Running CLI\n')
    CLI(net)
    info('*** Stopping network\n')
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    controller_ip = '127.0.0.1'
    run_custom_topology(controller_ip)
