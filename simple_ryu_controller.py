import numpy as np
import joblib
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib.packet import packet, ethernet, ipv4, tcp
from ryu.lib.packet import ether_types
from ryu.ofproto import ofproto_v1_3

class SimpleController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleController, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.clf = joblib.load('trained_model.joblib')

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Install the default table-miss flow entry
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]

        mod = parser.OFPFlowMod(datapath=datapath, priority=priority, match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        ip_pkt = pkt.get_protocol(ipv4.ipv4)
        tcp_pkt = pkt.get_protocol(tcp.tcp)

        if eth.ethertype == ether_types.ETH_TYPE_IP and ip_pkt and tcp_pkt:
            # Extract features from the packet
            pkt_size = len(msg.data)
            # Add more features as needed

            # Reshape the features to match the input shape of the model
            features = np.array([pkt_size]).reshape(1, -1)

            # Predict the label for the packet (1 for DDoS, 0 for normal)
            label = self.clf.predict(features)[0]

            if label == 1:
                # Handle DDoS packet
                self.handle_ddos_packet(datapath, msg, in_port)
                return
            else:
                # Handle normal packet
                self.handle_normal_packet(datapath, msg, in_port)
                return

        self.handle_unknown_packet(datapath, msg, in_port)

    def handle_ddos_packet(self, datapath, msg, in_port):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Redirect the attacker's traffic to a honeypot or sinkhole
        honeypot_port = 25  # Set the port number of the honeypot or sinkhole

        actions = [parser.OFPActionOutput(honeypot_port)]
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id, in_port=in_port, actions=actions)
        datapath.send_msg(out)
     
    def handle_normal_packet(self, datapath, msg, in_port):
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        dpid = datapath.id

        self.mac_to_port.setdefault(dpid, {})

        # Learn a MAC address to avoid FLOOD next time
        self.mac_to_port[dpid][eth.src] = in_port

        out_port = self.mac_to_port[dpid].get(eth.dst, datapath.ofproto.OFPP_FLOOD)

        # Construct action
        actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]

        # Install a flow to avoid packet-in next time
        if out_port != datapath.ofproto.OFPP_FLOOD:
            match = datapath.ofproto_parser.OFPMatch(in_port=in_port, eth_dst=eth.dst)
            self.add_flow(datapath, 1, match, actions)

        out = datapath.ofproto_parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id, in_port=in_port, actions=actions)
        datapath.send_msg(out)

    def handle_unknown_packet(self, datapath, msg, in_port):
        # Add your logic for handling packets that do not match the IP and TCP protocols in the example
        pass
