import os
import sys
import pandas as pd
from scapy.all import *

def preprocess_pcap(input_folder, output_file):
    features = []
    labels = []

    for filename in os.listdir(input_folder):
        filepath = os.path.join(input_folder, filename)
        packets = rdpcap(filepath)

        for packet in packets:
            # Extract features from the packet
            pkt_size = len(packet)
            # Add more features as needed

            # Label the packet (1 for DDoS, 0 for normal)
            label = 1 if is_ddos_packet(packet) else 0

            features.append([pkt_size])
            labels.append(label)

    df = pd.DataFrame(features, columns=['pkt_size'])
    df['label'] = labels

    df.to_csv(output_file, index=False)

def is_ddos_packet(packet):
    # Implement logic to determine if a packet is part of a DDoS attack
    pass

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input_folder> <output_file>")
        exit(1)

    input_folder = sys.argv[1]
    output_file = sys.argv[2]

    preprocess_pcap(input_folder, output_file)
#remember to run it
#python preprocess_data.py <input_folder> <output_file>
