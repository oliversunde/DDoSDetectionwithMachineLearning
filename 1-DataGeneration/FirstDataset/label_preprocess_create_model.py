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


def train_rf_classifier(input_file, output_file):
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
    print("feature_columns", feature_columns)
    # Define the parameter grid
    param_dist = {
        'n_estimators': [200,300,400, 500, 600, 700, 800, 900],
        'max_depth': [5, 10, 15, 20, 25, 30, 35, 40, 45],
        'min_samples_split': [2, 5, 10, 15],
        'min_samples_leaf': [1, 2, 3, 4, 5, 6, 7, 8]
    }
    # Create a DataFrame containing only the feature columns
    X = data[feature_columns]
    y = data['label']
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42)
    # Train a random forest classifier
    clf = RandomForestClassifier() #First time around, the line below second time around
    #clf = RandomForestClassifier(n_estimators=500, min_samples_split = 5, min_samples_leaf=1, max_depth=20, random_state=42)

    # Define the parameter grid
    # Initialize Randomized Search
    random_search = RandomizedSearchCV(estimator=clf, param_distributions=param_dist, cv=5, scoring='accuracy', n_jobs=-1)

    # Fit data to Randomized Search
    random_search.fit(X_train, y_train)

    # Best parameters after tuning
    print("Best Parameters: ", random_search.best_params_)

    # Evaluate the best model
    best_clf = random_search.best_estimator_
    # Fit data to Randomized Search
    #random_search.fit(X_train, y_train)

    # Best parameters after tuning
    #print("Best Parameters: ", random_search.best_params_)

    # Evaluate the best model
    #best_clf = random_search.best_estimator_
    clf.fit(X_train, y_train)

    # Evaluate the classifier on the test set
    y_pred = clf.predict(X_test)
    y_pred_proba = clf.predict_proba(X_test)[:, 1]

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


def preprocess_data(input_file, output_file):
    # Read the CSV file and specifying the column separator
    data = pd.read_csv(input_file, sep=',', dtype={'eth.src': str, 'eth.dst': str})
    # Convert the 'frame.time' column to pandas datetime object
    print(data.columns)
    data['_ws.col.Protocol'] = data['_ws.col.Protocol'].fillna('UNKNOWN')
    data['eth.src'] = data['eth.src'].fillna('00:00:00:00:00:00')
    data['eth.dst'] = data['eth.dst'].fillna('00:00:00:00:00:00')
    data = data.dropna(subset=['ip.src', 'ip.dst', 'eth.src', 'eth.dst'])
    print(("Shape of data after dropping NaN values:", data.shape))
    print("IP ADDRESS", data['ip.src'])

    def is_valid_ipv4_address(ip_str):
        try:
            ipaddress.IPv4Address(ip_str)
            return True
        except ipaddress.AddressValueError:
            return False
    data['ip.src'] = data['ip.src'].apply(lambda x: struct.unpack(
        "!L", socket.inet_aton(x))[0] if pd.notnull(x) and is_valid_ipv4_address(x) else 0)
    data['ip.dst'] = data['ip.dst'].apply(lambda x: struct.unpack(
        "!L", socket.inet_aton(x))[0] if pd.notnull(x) and is_valid_ipv4_address(x) else 0)
    # Convert MAC addresses to integers
    print(("Shape of data after handling IP addresses:", data.shape))
    data['eth.src'] = data['eth.src'].apply(
        lambda x: int(x.replace(':', ''), 16))
    data['eth.dst'] = data['eth.dst'].apply(
        lambda x: int(x.replace(':', ''), 16))

    def check_for_hex(data):
        hex_columns = []
        for column in data.columns:
            if data[column].apply(lambda x: isinstance(x, str) and x.startswith('0x')).any():
                hex_columns.append(column)
        return hex_columns
    print("Data after handling IP and MAC addresses:")
    print(data.head())

    def convert_hex_to_decimal(data, hex_columns):
        for column in hex_columns:
            data[column] = data[column].apply(lambda x: int(
                x, 16) if isinstance(x, str) and x.startswith('0x') else x)
        return data
    print("Data after converting hexadecimal values to decimal:")
    print(data.head())

    # Check for hexadecimal values
    hex_columns = check_for_hex(data)
    data = convert_hex_to_decimal(data, hex_columns)
    data.to_csv(output_file, index=False)
    print("data head 5")
    print(data.head(5))

def label_data(input_file, output_file):
    data = pd.read_csv(input_file)
    # Add a new column 'label' and set its value to 0 (normal) or 1 (DDoS) based on the source IP address
    data['label'] = 0
    #This was done manually
    ddos_ranges = [
        (10000, 17999),
        (28000, 102001)
    ]

    # Label the rows within the defined ranges as 1 (DDoS)
    for start, end in ddos_ranges:
        data.loc[start:end, 'label'] = 1

    # Label every number within the ranges as 1 (DDoS)
    for start, end in ddos_ranges:
            data.loc[start:end, 'label'] = 1

    # Save the labeled data
    data.to_csv(output_file, index=False)

if __name__ == '__main__':
    #preprocess_data('baada.csv', 'baada_preprocessed.csv')
    label_data('RAW.csv', 'labeled_RAW_data.csv')
    preprocess_data('labeled_RAW_data.csv','preprocessed_data.csv')
    train_rf_classifier('preprocessed_data.csv', 'random_forest_model.pkl')
