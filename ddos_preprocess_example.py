import os
import subprocess
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import RemoteController
from mininet.log import setLogLevel
from mininet.cli import CLI
import pandas as pd
import time

class CustomTopo(Topo):
    def build(self):
        # Add switches and hosts to the topology
        layer3_switch = self.addSwitch('s1')
        for i in range(1, 4):
            layer2_switch = self.addSwitch(f's1{i}')
            self.addLink(layer3_switch, layer2_switch)
            for j in range(1, 9):
                host = self.addHost(f'h{i}{j}')
                self.addLink(host, layer2_switch)

def start_network():
    # Start the Mininet network with the custom topology
    topo = CustomTopo()
    net = Mininet(topo=topo, controller=lambda name: RemoteController(name, ip='127.0.0.1'), autoSetMacs=True)
    net.start()

    # Start a basic Ryu controller
    ryu_controller = subprocess.Popen(['ryu-manager', 'ryu.app.simple_switch_13'])

    # Generate normal traffic using iperf
    net.get('h11').cmd('iperf -s &')
    net.get('h12').cmd('iperf -c h11 -t 100 &')

    # Generate DDoS traffic using hping3
    net.get('h21').cmd('hping3 --flood --rand-source h11 &')
    time.sleep(100)  # Generate traffic for 100 seconds

    # Capture network traffic
    tcpdump = subprocess.Popen(['tcpdump', '-i', 'any', '-w', 'network_traffic.pcap'])
    time.sleep(100)  # Capture network traffic for 100 seconds
    tcpdump.terminate()

    # Stop the Ryu controller and Mininet network
    ryu_controller.terminate()
    net.stop()

def convert_pcap_to_csv(pcap_file, csv_file):
    command = f"tshark -r {pcap_file} -T fields -e frame.number -e frame.time -e ip.src -e ip.dst -e tcp.srcport -e tcp.dstport -e frame.len -E header=y -E separator=, -E quote=d -E occurrence=f > {csv_file}"
    os.system(command)

def label_data(input_file, output_file):
    data = pd.read_csv(input_file)

    # Add a new column 'label' and set its value to 0 (normal) or 1 (DDoS) based on the source IP address
    data['label'] = 0
    data.loc[data['ip.src'] == '10.0.0.17', 'label'] = 1  # Assuming host h21 has IP address 10.0.0.17

    data.to_csv(output_file, index=False)

def preprocess_data(input_file, output_file):
    data = pd.read_csv(input_file)

    # Drop unnecessary columns
    data.drop(['frame.number', 'frame.time'], axis=1, inplace=True)

    # (Perform any additional preprocessing steps here, e.g., dealing with missing values or feature engineering)

    data.to_csv(output_file, index=False)
    if name == 'main':
    setLogLevel('info')

# Steps 1-4: Capture network traffic in the virtual network and convert it to CSV
start_network()
convert_pcap_to_csv('network_traffic.pcap', 'raw_network_data.csv')

# Step 5: Label the data
label_data('raw_network_data.csv', 'labeled_network_data.csv')

# Step 6: Clean and organize the data
preprocess_data('labeled_network_data.csv', 'preprocessed_network_data.csv')

print("Data preprocessing completed.")
  
