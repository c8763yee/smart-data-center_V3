import csv
import json
import paho.mqtt.client as mqtt
import pandas as pd
import os

from datetime import datetime

loc = {
    "2706/IAQ/1": "2706-IAQ-1",
    "2706/IAQ/2": "2706-IAQ-2",
    "2706/IAQ/3": "2706-IAQ-3",
    "2706/IAQ/1/control": "2706-IAQ-1-control",
    "2706/IAQ/2/control": "2706-IAQ-2-control",
    "2706/IAQ/3/control": "2706-IAQ-3-control",
    "2706/MeetingRoom/1": "2706-MeetingRoom-1",
    "2706/MeetingRoom/2": "2706-MeetingRoom-2",
    "2706/PowerBox": "2706-PowerBox",
    "2706/Air_Condiction/A": "2706-Air_Condiction-A",
    "2706/Air_Condiction/A/switch": "2706-Air_Condiction-A-status",
    "DL303/Info": "DL303"
}

MAX_ROWS = 1200
REMOVE_ROWS = 600

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to broker")
        client.subscribe("2706/#")
        client.subscribe("DL303/Info")
    else:
        print(f"Connection failed, return code={rc}")

def on_message(client, userdata, msg):
    # print(f"Topic: {msg.topic} - Message: {msg.payload.decode('utf-8')}")
    try:
        data = json.loads(msg.payload.decode("utf-8"))
        update_data(msg.topic, data)
    except Exception as e:
        print(f"MQTT Data Error: {e}")

def connect(MQTT_IP: str, MQTT_PORT: int):
    while True:
        try:
            client = mqtt.Client()
            client.on_connect = on_connect
            client.on_message = on_message
            client.connect(MQTT_IP, MQTT_PORT)
            client.loop_start()
            return client
        except Exception as e:
            print(f"MQTT Connection Error: {e}")

def save_csv(file_name, data):
    if not os.path.exists("csv"):
        os.makedirs("csv")
    file_path = f"csv/{file_name}.csv"
    file_exist = os.path.isfile(file_path)
    with open(file_path, "a", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exist:
            writer.writerow(data.keys())
        writer.writerow(data.values())
    if count_rows(file_path) > MAX_ROWS:
        remove_rows(file_path)

def count_rows(file_path):
    with open(file_path, "r", newline='', encoding="utf-8") as f:
        reader = csv.reader(f)
        row_count = sum(1 for row in reader)
    return row_count

def remove_rows(file_path):
    df = pd.read_csv(file_path)
    df = df.iloc[REMOVE_ROWS:]
    df.to_csv(file_path, index=False)

def update_data(key, value):
    # print(f"mqtt_data.py: {key} - {value}")
    if key in loc:
        value["datetime"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_csv(loc[key], value)
