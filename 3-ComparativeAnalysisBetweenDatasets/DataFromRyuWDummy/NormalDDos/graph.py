import pandas as pd
import matplotlib.pyplot as plt

# Read the CSV file skipping the first two rows
data = pd.read_csv('captured_network_dataNormDDoS.csv')

# Extract the required columns
frame_time_delta = data['frame_time_delta']
probabilities_1 = data['probability_1']
probabilities_2 = data['probability_2']
# Calculate the total capture time in seconds
total_time = frame_time_delta.sum()
print(total_time)

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

# Plotting the graph
plt.plot(x_coordinates, probabilities_1, label='Probability: Normal Traffic')
plt.plot(x_coordinates, probabilities_2, label='Probability: DDoS')
plt.xlabel(f'Time ({time_unit})')
plt.ylabel('Probability')
plt.title('First Dataset\n Random Forest 11 Features\n Normal-Burst-Normal-DDoS')
plt.legend()
plt.grid(True)
plt.show()
