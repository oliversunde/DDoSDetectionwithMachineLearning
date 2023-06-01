import time
import os
import random
import string
import signal
import subprocess
from custom_topology import CustomTopology, CustomRemoteController, run_custom_topology
from mininet.node import Node

with open('flag.txt', 'w') as f:
    f.write(str(True))
# commands = ['iperf', 'ping', 'hping3', 'ftp', 'dig', 'wget']


def generate_traffic(net):
    print("Pause 5 seconds so the RyuController has time to start after due to the Flag")
    time.sleep(5)
    print("generating traffic")
    # Hosts generating normal traffic
    h1 = net.getNodeByName('h1')
    h2 = net.getNodeByName('h2')
    h3 = net.getNodeByName('h3')
    h4 = net.getNodeByName('h4')
    h7 = net.getNodeByName('h7')
    h9 = net.getNodeByName('h9')
    h10 = net.getNodeByName('h10')
    h11 = net.getNodeByName('h11')
    h12 = net.getNodeByName('h12')
    h14 = net.getNodeByName('h14')
    h22 = net.getNodeByName('h22')
    h23 = net.getNodeByName('h23')
    # Hosts generating DDoS traffic
    h5 = net.getNodeByName('h5')
    h6 = net.getNodeByName('h6')
    h8 = net.getNodeByName('h8')
    h13 = net.getNodeByName('h13')
    h15 = net.getNodeByName('h15')
    h16 = net.getNodeByName('h16')
    h17 = net.getNodeByName('h17')
    # Burst of DDoS
    # Generate SYN flood
    h6.cmd('hping3 -c 100 -d 120 -S -w 64 -p 80 --flood --rand-source {} &'.format(h8.IP()))
    time.sleep(1)
    killl(net)
    print("SYN sleep 0.5")
    time.sleep(10)
    print("Slept for 10.5")
    # new burst
    h13.cmd(
        'hping3 -c 100 -d 120 -S -w 64 -p 80 --flood --rand-source {} &'.format(h15.IP()))
    time.sleep(1)
    killl(net)
    print("SYN sleep 0.5")
    time.sleep(10)
    print("Slept for 10.5")
    # new burst
    h13.cmd('hping3 -c 100 -d 120 -S -w 64 -p 80 --flood {} &'.format(h15.IP()))
    time.sleep(1)
    killl(net)
    time.sleep(10)
    # hping3 -2 -V -d 120 -w 64 --rand-source --flood


def process_exists(pid):
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True


def kill_process(pid):
    try:
        os.kill(pid, signal.SIGTERM)
        while process_exists(pid):
            time.sleep(0.1)
    except OSError:
        pass
    except ChildProcessError:
        pass


def killl(net):
    commands = ['hping3', 'ping', 'iperf', 'ftp',
                'dig', 'wget']  # Add other commands if needed
    for i in range(1, 25):
        host = net.get('h{}'.format(i))
        for command in commands:
            pid_output = host.cmd('pgrep -f ' + command)
            pids = pid_output.split()
            for pid in pids:
                if pid:  # Skip empty strings
                    try:
                        pid = int(pid)
                        process_cmdline = host.cmd(
                            'cat /proc/{}/cmdline'.format(pid)).strip()
                        if 'hping3' in process_cmdline:
                            print('Killing process:', process_cmdline)
                            kill_process(pid)
                        else:
                            print('Skipping process:', process_cmdline)
                    except (ProcessLookupError, ValueError):
                        pass


if __name__ == '__main__':
    controller_ip = '127.0.0.1'
    run_custom_topology(controller_ip, generate_traffic)
    with open('flag.txt', 'w') as f:
        f.write(str(False))
