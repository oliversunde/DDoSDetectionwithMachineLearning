import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Read the log file
with open('cpu_memory_log.txt', 'r') as file:
    lines = file.readlines()

# Process the lines
data_log = []
for line in lines:
    elements = line.split()
    datetime = elements[0][1:] + ' ' + elements[1][:-1]  # Extract date and time, remove brackets
    ryuCPU = float(elements[3][:-2])  # Extract ryuCPU, remove comma and percentage
    ryuMEM = float(elements[5][:-3])  # Extract ryuMEM, remove comma, 'MB' and the preceding digit
    hping3CPU = float(elements[7][:-2])  # Extract hping3CPU, remove comma and percentage
    hping3MEM = float(elements[9][:-3])  # Extract hping3MEM, remove comma, 'MB' and the preceding digit
    TotalCPU = float(elements[11][:-2])  # Extract TotalCPU, remove comma and percentage
    TotalMEM = float(elements[13][:-1])  # Extract TotalMEM, remove percentage

    data_log.append([datetime, ryuCPU, ryuMEM, hping3CPU, hping3MEM, TotalCPU, TotalMEM])

# Create dataframe
data_log = pd.DataFrame(data_log, columns=['DateTime', 'ryuCPU', 'ryuMEM', 'hping3CPU', 'hping3MEM', 'TotalCPU', 'TotalMEM'])

# Convert DateTime column to pandas datetime format
data_log['DateTime'] = pd.to_datetime(data_log['DateTime'])

# Plot
fig, ax = plt.subplots()
ax.plot(data_log['DateTime'], data_log['ryuCPU'], color='red', label='ryuCPU')
ax.set(xlabel='Time', ylabel='CPU Usage (%)', title='Ryu CPU Usage Over Time')
ax.xaxis.set_major_locator(mdates.MinuteLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
plt.show()

