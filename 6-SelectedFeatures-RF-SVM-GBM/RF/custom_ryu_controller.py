import cProfile
import threading
import joblib
import os
from ryu import cfg
from ryu.lib.packet import packet, ethernet, ipv4, tcp, udp, ipv6, icmp
from ryu.ofproto import ofproto_v1_3
from ryu.controller.handler import set_ev_cls
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller import ofp_event
from ryu.base import app_manager
from ryu.ofproto import ofproto_v1_3
from scapy.all import *
from sklearn.preprocessing import LabelEncoder
from itertools import islice
import configparser
import pickle
import argparse
import ipaddress
import numpy as np
import sys
import time
import struct
import socket
import csv
from collections import deque
sys.path.append('/home/mininet/toNull')
CONF = cfg.CONF

window_size = 1
window = deque()  # Init empty deque
unique_connections = set()
unique_packets_per_second = 0
with open('flag.txt', 'r') as f:
    flag = f.read().strip() == 'True'
    print("FLAG", flag)

class DummyModel:
    def predict(self, X):
        return np.zeros(X.shape[0], dtype=int)

    def predict_proba(self, X):
        return np.column_stack((np.ones(X.shape[0]), np.zeros(X.shape[0])))


class CustomRyuController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    EXPIRATION_TIME = 1

    def __init__(self, *args, **kwargs):
        self.ofp_version = ofproto_v1_3.OFP_VERSION
        super(CustomRyuController, self).__init__(*args, **kwargs)
        self.connections = {}  # initialize the attribute
        self.packet_count = 0
        self.packet_arrival_times = deque()
        self.packet_lengths = deque()
        self.identical_packets_per_second = deque()
        self.unique_packets_per_second = deque()
        self.expire_after = 5
        self.prev_packet_arrival_time = None
        self.protocol_encoder = LabelEncoder()
        self.ip_to_mac = {}
        self.malicious_macs = set()
        self.mac_to_port = {}
        self.buffer = []
        self.buffer_limit = 2000
        self.start_time = time.time()
        self.profiler = cProfile.Profile()
        if not flag:
            with open('random_forest_model.pkl', 'rb') as f:
                self.model = pickle.load(f)
        else:
            self.model = DummyModel()
        config = configparser.ConfigParser()
        config.read('ryu_config.conf')
        self.honeypot_port = int(config.get('honeypot', 'port'))

    def create_feature_array(self, features):
        try:
            ip_src = features.get('ip.src', '0.0.0.0') or '0.0.0.0'
            ip_dst = features.get('ip.dst', '0.0.0.0') or '0.0.0.0'
            try:
                ip_src = str(ipaddress.ip_address(ip_src))
            except ValueError:
                ip_src = '0.0.0.0'
            try:
                ip_dst = str(ipaddress.ip_address(ip_dst))
            except ValueError:
                ip_dst = '0.0.0.0'
            feature_array = np.array([
                features.get('identical_packets_per_second', 0),
                features.get('bytes_per_second', 0),
                features.get('unique_packets_per_second', 0),
                features.get('packet_arrival_rate', 0),
            ]).reshape(1, -1)
            return feature_array
        except Exception as e:
            self.logger.error("Error in create_feature_array: %s", e)
            return None

    def extract_features(self, pkt, frame_len):
        features = {}
        # Frame length
        features['frame.len'] = frame_len
        ip_src = None
        ip_dst = None
        if 'ip.src' in pkt:
            ip_src = pkt['ip.src']
        if 'ip.dst' in pkt:
            ip_dst = pkt['ip.dst']
        features['ip_src'] = ip_src
        features['ip_dst'] = ip_dst
        # Ethernet header
        eth = pkt.get_protocol(ethernet.ethernet)
        if eth:
            features['src_mac'] = int(eth.src.replace(':', ''), 16)
            features['dst_mac'] = int(eth.dst.replace(':', ''), 16)
            features['ethertype'] = eth.ethertype

        # IP header (both IPv4 and IPv6)
        ip_pkt = pkt.get_protocol(ipv4.ipv4)
        if ip_pkt:
            features['ip.src'] = ip_pkt.src
            features['ip.dst'] = ip_pkt.dst
            features['ip_proto'] = ip_pkt.proto
            features['ip_tos'] = ip_pkt.tos
            features['ip_ttl'] = ip_pkt.ttl
            features['ip_id'] = ip_pkt.identification
        else:
            ip6_pkt = pkt.get_protocol(ipv6.ipv6)
            if ip6_pkt:
                features['ip.src'] = ip6_pkt.src
                features['ip.dst'] = ip6_pkt.dst
                features['ip_nh'] = ip6_pkt.nxt
                features['ip_tc'] = ip6_pkt.traffic_class
                features['ip_hlim'] = ip6_pkt.hop_limit

        # TCP header
        tcp_pkt = pkt.get_protocol(tcp.tcp)
        if tcp_pkt:
            features['src_port'] = tcp_pkt.src_port
            features['dst_port'] = tcp_pkt.dst_port
            features['tcp_seq'] = tcp_pkt.seq
            features['tcp_ack'] = tcp_pkt.ack
            features['tcp_flags'] = tcp_pkt.bits
            features['tcp_window'] = tcp_pkt.window_size

        # UDP header
        udp_pkt = pkt.get_protocol(udp.udp)
        if udp_pkt:
            features['src_port'] = udp_pkt.src_port
            features['dst_port'] = udp_pkt.dst_port
            features['udp_len'] = udp_pkt.total_length

        # ICMP header
        icmp_pkt = pkt.get_protocol(icmp.icmp)
        if icmp_pkt:
            features['icmp_type'] = icmp_pkt.type
            features['icmp_code'] = icmp_pkt.code
        return features, tcp_pkt, udp_pkt, icmp_pkt

    @ set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(
            ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        inst = [parser.OFPInstructionActions(
            ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath=datapath, priority=0, match=match, instructions=inst)
        datapath.send_msg(mod)

    def update_connection_stats(self, connection_id, packet_size, current_time):
        if connection_id not in self.connections:
            self.connections[connection_id] = [current_time, 1, packet_size]
        else:
            prev_time, conn_packets, conn_bytes = self.connections[connection_id]
            conn_packets += 1
            conn_bytes += packet_size
            self.connections[connection_id] = [
                current_time, conn_packets, conn_bytes]

    def remove_expired_connections(self, current_time):

        before = len(self.connections)
        self.connections = {k: v for k, v in self.connections.items(
        ) if current_time - v[0] <= self.EXPIRATION_TIME}
        after = len(self.connections)

    def calculate_metrics(self, connection_id, current_time, packet_arrival_times, packet_lengths):
        # Remove expired packet arrival times and packet lengths
        self.packet_arrival_times = [
            t for t in self.packet_arrival_times if current_time - t <= self.EXPIRATION_TIME]
        if len(self.packet_arrival_times) > 0:
            start_index = len(packet_lengths) - len(self.packet_arrival_times)
            self.packet_lengths = deque(
                islice(self.packet_lengths, start_index, None))
        # Calculate Packet Arrival Rate
        packet_arrival_rate = 0
        if len(self.packet_arrival_times) > 1:
            time_diff = current_time - self.packet_arrival_times[0]
            packet_arrival_rate = (len(self.packet_arrival_times) - 1)
        # Calculate Bytes per Second
        bytes_per_second = 0
        if len(self.packet_lengths) > 1:
            byte_diff = sum(self.packet_lengths)
            time_diff = current_time - self.packet_arrival_times[0]
            bytes_per_second = byte_diff

        # Remove packets from the window that are older than the window size
        while window and current_time - window[0][0] >= window_size:
            window.popleft()

        # Check if the connection_id is identical to the connection_ids in the window
        identical_packets_per_second = sum(
            1 for _, conn_id in window if conn_id == connection_id)

        # Add the connection_id to the window
        window.append((current_time, connection_id))

        unique_packets_per_second = 0
        if len(self.connections) > 0:
            unique_connections = len(self.connections)
            time_diff = current_time - self.packet_arrival_times[0]
            unique_packets_per_second = unique_connections
        return packet_arrival_rate, bytes_per_second, unique_packets_per_second, identical_packets_per_second

    def write_to_csv(self, buffer, file_name):
        file_exists = os.path.isfile(file_name)
        header = ['eth.src', 'eth.dst', 'ip.src', 'ip.dst', 'frame.len', '_ws.col.Protocol', 'frame_time_delta', 'identical_packets_per_second',
                  'bytes_per_second', 'unique_packets_per_second', 'packet_arrival_rate', 'probability_1', 'probability_2']
        with open(file_name, mode='a') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(header)
            writer.writerows(buffer)

    def add_packet(self, eth_src, eth_dst, ip_src, ip_dst, frame_len, protocol, frame_time_delta, identical_packets_per_second, bytes_per_second, unique_packets_per_second, packet_arrival_rate, probabilities):
        # self.profiler.enable()
        # Flatten probabilities
        probabilities_flat = [
            prob for sublist in probabilities for prob in sublist]
        row = [eth_src, eth_dst, ip_src, ip_dst, frame_len, protocol, frame_time_delta, identical_packets_per_second,
               bytes_per_second, unique_packets_per_second, packet_arrival_rate] + probabilities_flat
        self.buffer.append(row)
        current_time = time.time()
        elapsed_time = current_time - self.start_time
        if len(self.buffer) >= self.buffer_limit:  # or elapsed_time
            threading.Thread(target=self.write_to_csv, args=(
                self.buffer, 'captured_network_data.csv')).start()
            self.buffer = []  # clear the buffer after writing to file
        # self.profiler.disable()
        # self.profiler.print_stats()

    def shut_down_port(self, datapath, port_no):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        port_config = ofproto.OFPPC_PORT_DOWN
        port_mask = ofproto.OFPPC_PORT_DOWN
        req = parser.OFPPortMod(datapath=datapath, port_no=port_no,
                                config=port_config, mask=port_mask)
        datapath.send_msg(req)

    def trace_back(self, dest_ip, source_mac):
        # Assume dest_ip is the IP address of the suspicious traffic
        # Let's find the MAC address corresponding to this IP
        dest_mac = self.ip_to_mac.get(dest_ip, None)
        self.malicious_macs.add(source_mac)
        if dest_mac is None:
            self.logger.info("IP address not found in the network")
            return

        # Search the path back
        for dpid, port_mac_dict in self.mac_to_port.items():
            if dest_mac in port_mac_dict:
                in_port = port_mac_dict[dest_mac]
                self.logger.info("Traffic from IP {} (MAC: {}) comes from port {} on switch {}".format(
                    dest_ip, dest_mac, in_port, dpid))

    def block_malicious_host(self, mac_address):
        # Find the switch and port connected to the malicious host
        switch_datapath, in_port = self.mac_to_port.get(
            mac_address, (None, None))
        # self.malicious_macs.add(source_mac)
        # print("malicious macs", malicious_macs)
        if switch_datapath is not None:
            ofproto = switch_datapath.ofproto
            parser = switch_datapath.ofproto_parser

            # Install a flow rule to drop all packets from the malicious host
            match = parser.OFPMatch(in_port=in_port, eth_src=mac_address)
            actions = []  # No actions means drop
            self.add_flow(switch_datapath, 1, match, actions)
            self.logger.info(f"Blocked link from host with MAC: {mac_address}")
        else:
            # for host in net.hosts:
            #    if host.MAC() == mac_address:
            #        match = parser.OFPMatch(
            #            in_port=in_port, eth_src=mac_address)
            actions = []  # No actions means drop
            #        self.add_flow(switch_datapath, 1, match, actions)
            self.logger.info(f"Blocked link from host with MAC: {mac_address}")
            self.logger.warning(
                f"Host with MAC: {mac_address} not found in mac_to_port")

    @ set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        self.packet_count += 1
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        dst = eth.dst
        src = eth.src
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]
        # Install a flow to avoid FLOOD next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            self.add_flow(datapath, 1, match, actions)

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)
        # Learn a MAC address to avoid FLOOD next time
        self.mac_to_port[dpid][src] = in_port
        frame_len = len(msg.data)
        self.packet_lengths.append(frame_len)
        # Extract packet features
        features, tcp_pkt, udp_pkt, icmp_pkt = self.extract_features(
            pkt, frame_len)
        src_ip = str(features.get('ip.src'))
        dst_ip = str(features.get('ip.dst'))
        src_port = str(features.get('src_port'))
        dst_port = str(features.get('dst_port'))
        current_time = time.time()
        self.packet_arrival_times.append(current_time)
        frame_time_delta = current_time - \
            self.prev_packet_arrival_time if self.prev_packet_arrival_time is not None else 0
        self.prev_packet_arrival_time = current_time
        bytes_ = len(msg.data)
        proto = None
        if tcp_pkt:
            proto = "TCP"
        elif udp_pkt:
            proto = "UDP"
        elif icmp_pkt:
            proto = "ICMP"
        features['_ws.col.Protocol'] = proto
        if dst_port:
            connection_id = (src, dst, src_ip, dst_ip, dst_port)
        else:
            connection_id = (src, dst, src_ip, dst_ip, 'default')
        # connection_id = (src, dst, src_ip, dst_ip, dst_port)

        identical_conn_count = 0
        unique_conn_count = 0
        # update the connections dictionary
        self.update_connection_stats(connection_id, bytes_, current_time)
        self.prev_packet_arrival_time = current_time

        self.remove_expired_connections(current_time)

        packet_arrival_rate, bytes_per_second, unique_packets_per_second, identical_packets_per_second = self.calculate_metrics(
            connection_id, current_time, self.packet_arrival_times, self.packet_lengths)
        feature_array = self.create_feature_array({
            'identical_packets_per_second': identical_packets_per_second,
            'bytes_per_second': bytes_per_second,
            'unique_packets_per_second': unique_packets_per_second,
            'packet_arrival_rate': packet_arrival_rate,
        })
        probabilities = self.model.predict_proba(feature_array)
        # print(probabilities)
        # print(packet_arrival_rate)
        self.add_packet(eth.src, eth.dst, src_ip, dst_ip, frame_len, proto, frame_time_delta, identical_packets_per_second,
                        bytes_per_second, unique_packets_per_second, packet_arrival_rate, probabilities)
        # probabilities = self.model.predict_proba(feature_array)
        pkt_ipv4 = pkt.get_protocol(ipv4.ipv4)
        pkt_ethernet = pkt.get_protocol(ethernet.ethernet)
        confidence_threshold = 0.8  # endre litt kanskje
        prediction = 1 if probabilities[0][1] >= confidence_threshold else 0
        if not flag:
            if prediction == 1:  # DDoS traffic detected
                out_port = self.mac_to_port[dpid].get(dst, ofproto.OFPP_FLOOD)
                actions = [parser.OFPActionOutput(out_port)]
            else:
                out_port = self.mac_to_port[dpid].get(dst, ofproto.OFPP_FLOOD)
                actions = [parser.OFPActionOutput(out_port)]
                # self.logger.info("Normal traffic forwarded from %s to %s.", eth.src, eth.dst)
        else:
            out_port = self.mac_to_port[dpid].get(dst, ofproto.OFPP_FLOOD)
            actions = [parser.OFPActionOutput(out_port)]

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=ins, idle_timeout=75)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)
