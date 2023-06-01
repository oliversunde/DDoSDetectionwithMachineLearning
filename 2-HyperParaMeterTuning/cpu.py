import psutil
import time


def get_cpu_usage():
    cpu_percentage = psutil.cpu_percent(interval=1)
    return cpu_percentage


def get_memory_usage():
    memory = psutil.virtual_memory()
    memory_percentage = memory.percent
    return memory_percentage


def get_process_pid(process_name):
    for proc in psutil.process_iter(['name', 'pid']):
        if proc.info['name'] == process_name:
            return proc.info['pid']
    return None


def get_process_cpu_memory(pid):
    process = psutil.Process(pid)
    cpu_percentage = process.cpu_percent(interval=1)
    memory_info = process.memory_info()
    memory_usage = memory_info.rss / 2**20  # Convert to MB
    return cpu_percentage, memory_usage


file_path = "cpu_memory_log.txt"

# Specify the process name you want to monitor
process_name = "ryu-manager"

while True:
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    # Get the PID of the specified process
    pid = get_process_pid(process_name)
    if pid is not None:
        process_cpu_percentage, process_memory_usage = get_process_cpu_memory(
            pid)
        total_cpu_percentage = get_cpu_usage()
        total_memory_percentage = get_memory_usage()
        log_line = f"[{current_time}] ryuCPU: {process_cpu_percentage}%, ryuMEM: {process_memory_usage} MB, totCPU: {total_cpu_percentage}%, totMEM: {total_memory_percentage}%\n"
        with open(file_path, "a") as file:
            file.write(log_line)
    else:
        print(f"[{current_time}] {process_name} is not running.")
    time.sleep(1)
