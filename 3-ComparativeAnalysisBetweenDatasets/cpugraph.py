import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.dates import date2num
import datetime

# Define a function to parse the date and time from the log entries
def parse_date(date_string):
    return datetime.datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')

# Read the log file and parse the data
data_log = pd.read_csv('cpu_memory_log.txt', sep=' ', header=None)
data_log.columns = ['Date', 'Time', 'ryuCPU', 'ryuMEM', 'hping3CPU', 'hping3MEM', 'TotalCPU', 'TotalMEM']

# Parse the ryu CPU usage to just the numeric value
data_log['ryuCPU'] = data_log['ryuCPU'].str.replace('ryuCPU:', '').str.replace('%,', '').astype(float) / 100

# Parse the date and time to a datetime object
data_log['DateTime'] = data_log['Date'] + ' ' + data_log['Time']
data_log['DateTime'] = data_log['DateTime'].apply(parse_date)

# Convert the datetime to a number so it can be plotted
data_log['DateTime'] = date2num(data_log['DateTime'])

# Read the CSV file skipping the first two rows
data_csv = pd.read_csv('captured_network_data1.csv')

# Extract the required columns
frame_time_delta = data_csv['frame_time_delta']
probabilities_1 = data_csv['probability_1']
probabilities_2 = data_csv['probability_2']

# Calculate the total capture time in seconds
total_time = frame_time_delta.sum()

# Convert frame time delta to seconds or minutes
if total_time >= 60:
    frame_time_delta = frame_time_delta/60  # Convert to minutes
    time_unit = 'Minutes'
else:
    time_unit = 'Seconds'

# Initialize variables for cumulative sum and x-coordinates
cumulative_sum = 0
x_coordinates = []

# Calculate cumulative sum and create x-coordinates
for delta in frame_time_delta:
    cumulative_sum += delta
    x_coordinates.append(cumulative_sum)

# Plotting the graphs
fig, ax1 = plt.subplots()

ax1.set_xlabel('Time ({})'.format(time_unit))
ax1.set_ylabel('Probability', color='tab:blue')
ax1.plot(x_coordinates, probabilities_1, color='tab:blue', label='Probability: Normal Traffic')
ax1.plot(x_coordinates, probabilities_2, color='tab:orange', label='Probability: DDoS')
ax1.tick_params(axis='y', labelcolor='tab:blue')

ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

ax2.set_ylabel('Ryu CPU Usage', color='tab:red')  # we already handled the x-label with ax1
ax2.plot_date(data_log['DateTime'], data_log['ryuCPU'], 'r-', label='Ryu CPU Usage')
ax2.tick_params(axis='y', labelcolor='tab:red')

fig.tight_layout()  # otherwise the right y-label is slightly clipped
plt.title('First Dataset\n Random Forest 11 Features\n Normal -2xDDoS Burst - Normal - DDoS')
fig.legend(loc='upper right')
plt.grid(True)
plt.show()

