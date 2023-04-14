import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

# Step 8: Load the labeled network traffic data
data = pd.read_csv('labeled_data.csv')

# Step 9: Split the data into features (X) and labels (y)
X = data.drop('label', axis=1)
y = data['label']

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Step 10: Train the machine learning model
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_train)

# Step 11: Test the system
y_pred = clf.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"Accuracy: {accuracy:.2f}")

print("Classification Report:")
print(classification_report(y_test, y_pred))

# Save the trained model
import joblib
joblib.dump(clf, 'random_forest_model.pkl')

# Test with a sample network traffic data
sample_data = pd.DataFrame({"feature1": [value1], "feature2": [value2], ..., "featureN": [valueN]})
prediction = clf.predict(sample_data)
print("Prediction for the sample data: ", prediction)
