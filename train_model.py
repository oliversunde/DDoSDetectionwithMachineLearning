import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib

# Load the dataset
data = pd.read_csv("network_data.csv")

# Preprocess and label the network traffic data
# Assume that the dataset has a column named 'label' with values 0 (normal) or 1 (DDoS)
X = data.drop("label", axis=1)
y = data["label"]

# Split the dataset into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# Train the RandomForest classifier
clf = RandomForestClassifier()
clf.fit(X_train, y_train)

# Save the trained model to a file
joblib.dump(clf, 'trained_model.joblib')
