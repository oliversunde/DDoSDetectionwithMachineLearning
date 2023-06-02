import pandas as pd
import matplotlib.pyplot as plt

# Read the CSV file skipping the first two rows
data = pd.read_csv('captured_network_data.csv')

# Extract the required columns
frame_time_delta = data['frame_time_delta']
probabilities_1 = data['probability_1']
probabilities_2 = data['probability_2']

# Calculate the total capture time in seconds
total_time = frame_time_delta.sum()
print(total_time)

# Convert frame time delta to seconds or minutes
if total_time >= 60:
    frame_time_delta = frame_time_delta / 60  # Convert to minutes
    time_unit = 'Minutes'
else:
    time_unit = 'Seconds'

# Initialize variables for cumulative sum and x-coordinates
cumulative_sum = 0
x_coordinates = []
filtered_probabilities_1 = []  # Store filtered probabilities 1
filtered_probabilities_2 = []  # Store filtered probabilities 2

# Calculate cumulative sum and create x-coordinates
for delta, prob1, prob2 in zip(frame_time_delta, probabilities_1, probabilities_2):
    if delta <= 0.5:  # Skip plotting if frame_time_delta exceeds the threshold (e.g., 1)
        cumulative_sum += delta
        x_coordinates.append(cumulative_sum)
        filtered_probabilities_1.append(prob1)
        filtered_probabilities_2.append(prob2)
    else:
        # Add None values to create a gap in the plot
        x_coordinates.extend([None, cumulative_sum])
        filtered_probabilities_1.extend([None, prob1])
        filtered_probabilities_2.extend([None, prob2])

# Plotting the graph
plt.plot(x_coordinates, filtered_probabilities_1, label='Probability: Normal Traffic')
plt.plot(x_coordinates, filtered_probabilities_2, label='Probability: DDoS')
plt.xlabel(f'Time ({time_unit})')
plt.ylabel('Probability')
plt.title('Gradient Boosting Classifier with four selected features\n Normal -2xDDoS Burst - Normal - DDoS')
plt.legend()
plt.grid(True)
plt.show()

