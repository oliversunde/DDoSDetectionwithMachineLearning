from sklearn.metrics import confusion_matrix, classification_report, roc_auc_score, accuracy_score, precision_score
import matplotlib.pyplot as plt
import re
from datetime import datetime
import numpy as np
import pandas as pd
import pickle
from sklearn.model_selection import RandomizedSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn import svm
from sklearn.inspection import permutation_importance
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, classification_report
from custom_topology import CustomTopology
from mininet.topo import Topo
from mininet.link import TCLink
from mininet.util import dumpNodeConnections
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.node import RemoteController
from mininet.net import Mininet
import os
import subprocess
import time
import ipaddress
import socket
import struct
import sys
import random
import string
import threading
import signal
import joblib

def run_feature_ranking(input_file, output_file):
    data = pd.read_csv(input_file)
    missing_values = data.isnull().sum()
    print("Number of missing values in each feature:")
    print(missing_values)
    data = data.dropna()
    data = data.replace([np.inf, -np.inf], np.finfo(np.float32).max)
    missing_values = data.isnull().sum()
    print("Number of missing values in each feature:")
    print(missing_values)
    num_packets = len(data)
    print("Number of packets (rows) in the DataFrame:", num_packets)
    protocol_encoder = LabelEncoder()
    data['_ws.col.Protocol'] = protocol_encoder.fit_transform(data['_ws.col.Protocol'])
    # Split the data into training and test sets
    # Define the columns you want to use as features
    feature_columns = [
        "eth.src",
        "eth.dst",
        "ip.src",
        "ip.dst",
        "frame.len",
        "_ws.col.Protocol",
        "frame_time_delta",
        "identical_packets_per_second",
        "bytes_per_second",
        "unique_packets_per_second",
        "packet_arrival_rate",
    ]
    # Create a DataFrame containing only the feature columns
    X = data[feature_columns]
    y = data['label']
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42)

    clf = RandomForestClassifier(n_estimators=400,min_samples_split=10, min_samples_leaf=3, max_depth=45)
    clf.fit(X_train, y_train)

    # Evaluate the classifier on the test set
    y_pred = clf.predict(X_test)
    y_pred_proba = clf.predict_proba(X_test)[:, 1]
    # Assume clf is your trained model
    importances = clf.feature_importances_

    # Sort feature importances in descending order
    indices = np.argsort(importances)[::-1]
    # Rearrange feature names so they match the sorted feature importances
    names = [feature_columns[i] for i in indices]

    for f in range(X.shape[1]): # X being your dataframe with the features
        print("%d. feature %d (%f)" % (f + 1, indices[f], importances[indices[f]]))

    # Plot the feature importances of the forest
    plt.figure(figsize=(10,8))
    plt.title("Feature importances Random Forest Model")
    plt.bar(range(X.shape[1]), importances[indices], color="r", align="center")
    plt.xticks(range(X.shape[1]), names, rotation=90)
    plt.xlim([-1, X.shape[1]])
    plt.show()


    print(confusion_matrix(y_test, y_pred))
    print(classification_report(y_test, y_pred))

    # Compute and print ROC-AUC score
    roc_auc = roc_auc_score(y_test, y_pred_proba)
    print(f"ROC-AUC score: {roc_auc}")

    # Compute and print Accuracy
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Accuracy: {accuracy}")

    # Compute and print Precision
    precision = precision_score(y_test, y_pred)
    print(f"Precision: {precision}")

    print(confusion_matrix(y_test, y_pred))
    print(classification_report(y_test, y_pred))

    # Save the trained model
    with open(output_file, 'wb') as f:
        pickle.dump(clf, f, protocol=2)

if __name__ == '__main__':
    run_feature_ranking('preprocessed_data.csv', 'random_forest_model.pkl')
