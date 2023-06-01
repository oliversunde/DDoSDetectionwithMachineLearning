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
    
#commands = ['iperf', 'ping', 'hping3', 'ftp', 'dig', 'wget']
def generate_traffic(net):
    print("Pause 5 seconds so the RyuController has time to start after due to the Flag")
    time.sleep(5)
    print("generating traffic")
    #Hosts generating normal traffic
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
    #Hosts generating DDoS traffic
    h5 = net.getNodeByName('h5')
    h6 = net.getNodeByName('h6')
    h8 = net.getNodeByName('h8')
    h13 = net.getNodeByName('h13')
    h15 = net.getNodeByName('h15')
    h16 = net.getNodeByName('h16')
    h17 = net.getNodeByName('h17')
    print("vsftpd")
    h22.cmd('echo "anonymous_enable=YES" >> /etc/vsftpd.conf')
    h22.cmd('echo "anon_upload_enable=YES" >> /etc/vsftpd.conf')
    h22.cmd('echo "anon_mkdir_write_enable=YES" >> /etc/vsftpd.conf')
    h22.cmd('service vsftpd start')
    print("service vsftpd started")
    # Start an iperf server on h2
    h2.cmd('iperf -s &')
    print("iperf -s & started on h2 - create udp/tcp traffic from h1 to h2")
    time.sleep(5)
    print(h2.cmd('ps aux | grep iperf')) #check if the server is indeed running
    print("slept for 5, starting TCP iperf")
    # Create TCP and UDP traffic from h1 to h2
    h1.cmd('iperf -c ' + h2.IP() + ' -t 10 -i 1 &')
    time.sleep(9)  # Delay to ensure the TCP test finishes
    print(h1.cmd('ps aux | grep iperf'))
    print("iperf udp starting, finished 15s sleep")
    h1.cmd('iperf -c ' + h2.IP() + ' -t 10 -i 1 -u &')
    time.sleep(9)
    print(h1.cmd('ps aux | grep iperf')) # check if client is indeed running iperf
    time.sleep(6)
    print("after 15sec sleep/iperf udp, now pingall")
    # Ping from all hosts to all hosts except attacking hosts - labeling..
    for i in range(1, 25):
        if i not in [5, 6, 8, 13, 15, 16, 17]:  # Exclude specific hosts
            current_host = net.getNodeByName('h{}'.format(i))
            for j in range(1, 25):
                if j != i and j not in [5, 6, 8, 13, 15, 16, 17]:  # Exclude specific hosts
                    target_host = net.getNodeByName('h{}'.format(j))
                    current_host.cmd('ping -c 1 ' + target_host.IP() + ' &')
                    time.sleep(0.2)  # 0.02-second delay between each ping

    print("etter pingall")
    time.sleep(10)
    print("time sleep 10")
    time.sleep(10)
    print("etter 20 sec søvn")
    # Generate TCP and UDP traffic with iperf
    print("TCP Traffic Generation")
    # TCP traffic
    h3.cmd('iperf -s &')  # h3 acts as server
    h9.cmd('iperf -s &')  # h9 acts as server
    print(h3.cmd('ps aux | grep iperf'))
    print(h9.cmd('ps aux | grep iperf'))
    time.sleep(15)
    h7.cmd('iperf -c ' + h3.IP() + ' -t 10 -i 1 &')  # h7 acts as client
    h10.cmd('iperf -c ' + h9.IP() + ' -t 10 -i 1 &') # h10 acts as client
    time.sleep(9)
    print(h7.cmd('ps aux | grep iperf'))
    print(h10.cmd('ps aux | grep iperf'))
    time.sleep(6)
    print("UDP Traffic Generation")
    # UDP traffic
    h4.cmd('iperf -s -u -p 5002 &')  # h4 acts as server
    h11.cmd('iperf -s -u -p 5004 &')  # h11 acts as server
    time.sleep(15)
    print(h4.cmd('ps aux | grep iperf'))
    print(h11.cmd('ps aux | grep iperf'))
    h1.cmd('iperf -c ' + h4.IP() + ' -t 10 -i 1 -u &')  # h1 acts as client
    h12.cmd('iperf -c ' + h11.IP() + ' -t 10 -i 1 -u &') # h12 acts as client
    time.sleep(9)
    print(h1.cmd('ps aux | grep iperf'))
    print(h12.cmd('ps aux | grep iperf'))
    time.sleep(6)
    
    #Burst of DDoS
    # Generate SYN flood
    h6.cmd('hping3 -c 10000 -d 120 -S -w 64 -p 80 --flood --rand-source {} &'.format(h8.IP()))
    time.sleep(1)
    killl(net)
    print("SYN sleep 0.5")
    time.sleep(10)
    print("Slept for 10.5")
    #new burst
    h13.cmd('hping3 -c 10000 -d 120 -S -w 64 -p 80 --flood --rand-source {} &'.format(h15.IP()))
    time.sleep(1)
    killl(net)
    print("SYN sleep 0.5")
    killl(net)
    time.sleep(10)
    print("Slept for 10.5")
    print("Ping alot")
    #New round of pings
    for i in range(1, 25):
        if i not in [5, 6, 8, 13, 15, 16, 17]:  # Exclude specific hosts
            current_host = net.getNodeByName('h{}'.format(i))
            for j in range(1, 25):
                if j != i and j not in [5, 6, 8, 13, 15, 16, 17]:  # Exclude specific hosts
                    target_host = net.getNodeByName('h{}'.format(j))
                    current_host.cmd('ping -c 1 ' + target_host.IP() + ' &')
                    time.sleep(0.2)  # 0.02-second delay between each ping

    # Generate HTTP traffic (wget)
    print("WGET www.example.com")
    h14.cmd('wget www.example.com')
    h1.cmd('wget www.example.com')
    time.sleep(5)
    print("DIG www.example.com")
    # Generate DNS queries (dig)
    h10.cmd('dig www.example.com')
    h2.cmd('dig www.example.com')
    time.sleep(5)
    print("FTP h23 -> h22")
    # FTP test
    h23.cmd('ftp -n ' + h22.IP() + '<<EOF\nuser anonymous nopassword\nls\nquit\nEOF')
    
    print("Start 10s SYN FLOOD")
    # Generate SYN flood
    h6.cmd('hping3 -c 10000 -d 120 -S -w 64 -p 80 --flood --rand-source {} &'.format(h8.IP()))
    time.sleep(10)
    killl(net)
    print("KILL Command initiated to kill SYN FLOOD")
    print("Start 10s UDP FLOOD")
    # Generate UDP flood
    h13.cmd(
        'hping3 -c 10000 -d 120 -2 -w 64 -p 80 --flood --rand-source {} &'.format(h17.IP()))
    time.sleep(10)
    killl(net)
    print("KILL Command initiated to kill UDP FLOOD")

    print("Start 10s HTTP FLOOD")
    random_path = ''.join(random.sample(
        string.ascii_letters + string.digits, 10))
    h5.cmd('hping3 -c 10000 -d 120 -S -w 64 -p 80 -E /dev/urandom --flood --rand-source {} -k, /{}'.format(h6.IP(), random_path))
    time.sleep(10)
    killl(net)
    print("KILL Command initiated to kill HTTP FLOOD")
    print("Start 10s ICMP FLOOD")
    # Generate ICMP flood
    icmp_cmd = 'timeout 10s hping3 -1 --flood -a {} {}'.format(h13.IP(), h15.IP())
    icmp_process = subprocess.Popen(icmp_cmd, shell=True)
    icmp_process.wait()
    time.sleep(10)
    if icmp_process.returncode == 0:
        print("ICMP FLOOD COMPLETED")
    else:
        print("ICMP FLOOD TIMEOUT AND KILL INITIATED")
        killl(net)
    
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
    commands = ['hping3']  # Add other commands if needed
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
