import pandas as pd
import matplotlib.pyplot as plt

# Read the first CSV file
data1 = pd.read_csv('captured_network_data.csv')

# Read the second CSV file
data2 = pd.read_csv('captured_network_datawoblock.csv')

# Extract the required columns from the first file
frame_time_delta_1 = data1['frame_time_delta']
probabilities_1_1 = data1['probability_1']
probabilities_2_1 = data1['probability_2']
packet_arrival_rate_1 = data1['packet_arrival_rate']

# Extract the required columns from the second file
frame_time_delta_2 = data2['frame_time_delta']
probabilities_1_2 = data2['probability_1']
probabilities_2_2 = data2['probability_2']
packet_arrival_rate_2 = data2['packet_arrival_rate']

# Calculate the total capture time in seconds for the first file
total_time_1 = frame_time_delta_1.sum()
print(total_time_1)

# Calculate the total capture time in seconds for the second file
total_time_2 = frame_time_delta_2.sum()
print(total_time_2)

# Convert frame time delta to seconds or minutes for the first file
if total_time_1 >= 60:
    frame_time_delta_1 = frame_time_delta_1 / 60  # Convert to minutes
    time_unit_1 = 'Minutes'
else:
    time_unit_1 = 'Seconds'

# Convert frame time delta to seconds or minutes for the second file
if total_time_2 >= 60:
    frame_time_delta_2 = frame_time_delta_2 / 60  # Convert to minutes
    time_unit_2 = 'Minutes'
else:
    time_unit_2 = 'Seconds'

# Initialize variables for cumulative sum and x-coordinates for the first file
cumulative_sum_1 = 0
x_coordinates_1 = []

# Calculate cumulative sum and create x-coordinates for the first file
for delta in frame_time_delta_1:
    cumulative_sum_1 += delta
    x_coordinates_1.append(cumulative_sum_1)

# Initialize variables for cumulative sum and x-coordinates for the second file
cumulative_sum_2 = 0
x_coordinates_2 = []

# Calculate cumulative sum and create x-coordinates for the second file
for delta in frame_time_delta_2:
    cumulative_sum_2 += delta
    x_coordinates_2.append(cumulative_sum_2)

# Plotting the graph
plt.plot(x_coordinates_1, packet_arrival_rate_1, label='Packet Arrival Rate Blocking', color='red')
plt.plot(x_coordinates_2, packet_arrival_rate_2, label='Packet Arrival Without Block', color='blue')
plt.xlabel(f'Time (s)')
plt.ylabel('Packet Arrival Rate')
plt.title('GBM: Packet Arrival Rate')
plt.legend()
plt.grid(True)
plt.show()
