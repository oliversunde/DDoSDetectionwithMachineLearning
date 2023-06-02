import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MultipleLocator

# Read the CPU and memory log file
with open('cpu_memory_log1.txt', 'r') as file:
    lines = file.readlines()

# Process the lines
data_log = []
cpu_time = 0  # Initialize CPU time as 0
for line in lines:
    elements = line.split()
    datetime = elements[0][1:] + ' ' + elements[1][:-1]  # Extract date and time, remove brackets
    ryuCPU = float(elements[3][:-2])  # Extract ryuCPU, remove comma and percentage
    ryuMEM = float(elements[5][:-3])  # Extract ryuMEM, remove comma, 'MB' and the preceding digit
    hping3CPU = float(elements[7][:-2])  # Extract hping3CPU, remove comma and percentage
    hping3MEM = float(elements[9][:-3])  # Extract hping3MEM, remove comma, 'MB' and the preceding digit
    TotalCPU = float(elements[11][:-2])  # Extract TotalCPU, remove comma and percentage
    TotalMEM = float(elements[13][:-1])  # Extract TotalMEM, remove percentage

    # Adjust the time for the first CPU data point to be zero
    if cpu_time == 0:
        cpu_time = pd.to_datetime(datetime)  # Convert to datetime format
    datetime = (pd.to_datetime(datetime) - cpu_time).total_seconds()  # Calculate time difference in seconds

    data_log.append([datetime, ryuCPU, ryuMEM, hping3CPU, hping3MEM, TotalCPU, TotalMEM])

# Create dataframe for CPU and memory log
data_log = pd.DataFrame(data_log, columns=['Time', 'ryuCPU', 'ryuMEM', 'hping3CPU', 'hping3MEM', 'TotalCPU', 'TotalMEM'])

# Read the network data CSV file
data = pd.read_csv('captured_network_data1337.csv')

# Extract the required columns
frame_time_delta = data['frame_time_delta']
probabilities_1 = data['probability_1']
probabilities_2 = data['probability_2']

# Convert frame time delta to cumulative time in seconds
time = frame_time_delta.cumsum()

# Plotting the graph
fig, ax1 = plt.subplots()

# Create a second y-axis for network data probabilities
ax2 = ax1.twinx()
ax2.plot(time, probabilities_1, label='Probability: Normal Traffic', color='blue')
ax2.plot(time, probabilities_2, label='Probability: DDoS', color='orange')
ax2.set_ylabel('Probability')
ax2.tick_params('y')

# Plot CPU Usage over time on top
ax1.plot(data_log['Time'], data_log['ryuCPU'], color='red', label='ryuCPU', zorder=10)
ax1.set_ylabel('CPU Usage (%)', color='red')
ax1.tick_params('y', colors='red')

# Set x-axis formatting
ax1.set_xlabel('Time (s)')
ax1.xaxis.set_major_locator(MultipleLocator(60))  # Set tick every 60 seconds
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))

# Set title and legend
plt.title('Combined Graph: CPU Usage and Network Data Probabilities')
lines = ax1.get_lines() + ax2.get_lines()
plt.legend(lines, [line.get_label() for line in lines])

# Display the plot
plt.show()

