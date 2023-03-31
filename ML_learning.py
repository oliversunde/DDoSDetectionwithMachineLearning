import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

# Load the preprocessed dataset
data = pd.read_csv('preprocessed_data.csv')

# Split the dataset into features (X) and labels (y)
X = data.drop('label', axis=1)
y = data['label']

# Split the dataset into a training and testing set
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Create a RandomForest classifier and train it with the training data
clf = RandomForestClassifier()
clf.fit(X_train, y_train)

# Predict the labels for the test set
y_pred = clf.predict(X_test)

# Calculate the accuracy score
accuracy = accuracy_score(y_test, y_pred)

# Visualize the accuracy score
plt.bar(['Accuracy'], [accuracy], color=['blue'])
plt.ylim(0, 1)
plt.ylabel('Score')
plt.title('Accuracy Score')
plt.show()
