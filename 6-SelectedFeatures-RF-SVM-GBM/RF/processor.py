import psutil
import time


def get_cpu_usage():
    cpu_percentage = psutil.cpu_percent(interval=1)
    return cpu_percentage


def get_memory_usage():
    memory = psutil.virtual_memory()
    memory_percentage = memory.percent
    return memory_percentage


def get_process_pids(process_name):
    pids = []
    for proc in psutil.process_iter(['name', 'pid']):
        if process_name in proc.info['name']:
            pids.append(proc.info['pid'])
    return pids


def get_process_cpu_memory(pid):
    process = psutil.Process(pid)
    cpu_percentage = process.cpu_percent(interval=1)
    memory_info = process.memory_info()
    memory_usage = memory_info.rss / 2**20  # Convert to MB
    return cpu_percentage, memory_usage


file_path = "cpu_memory_log.txt"

# Specify the process names you want to monitor
process_name_ryu = "ryu-manager"
#process_name_hping3 = "hping3"

while True:
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    
    # Get the PIDs of the ryu-manager and hping3 processes
    pid_ryu = get_process_pids(process_name_ryu)
    #   pids_hping3 = get_process_pids(process_name_hping3)
    
    total_cpu_percentage = get_cpu_usage()
    total_memory_percentage = get_memory_usage()
    
    if pid_ryu:
        ryu_cpu_percentage, ryu_memory_usage = get_process_cpu_memory(pid_ryu[0])
    else:
        ryu_cpu_percentage, ryu_memory_usage = 0, 0
    
    #hping3_cpu_percentage, hping3_memory_usage = 0, 0
    #if pids_hping3:
    #    for pid in pids_hping3:
    #        cpu, mem = get_process_cpu_memory(pid)
    #        hping3_cpu_percentage += cpu
    #        hping3_memory_usage += mem

    log_line = f"[{current_time}] ryuCPU: {ryu_cpu_percentage}%, ryuMEM: {ryu_memory_usage}MB, hping3CPU: {ryu_memory_usage}%, hping3MEM: {ryu_memory_usage}MB, TotalCPU: {total_cpu_percentage}%, TotalMEM: {total_memory_percentage}%\n"
    with open(file_path, "a") as file:
        file.write(log_line)
    
    time.sleep(1)

