import json
import pandas as pd

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from taipy.gui import Gui, Markdown, notify, State, invoke_callback, get_state_id

from mqtt_data import connect
from configs import *

# 折線圖X/Y軸屬性
property_chart_tc = {
    "x": "datetime",
    "y[1]": "Temperature",
    "color[1]": "blue",
    "type[1]": "line"
}

property_chart_humi = {
    "x": "datetime",
    "y[1]": "Humidity",
    "color[1]": "blue",
    "type[1]": "line"
}

property_chart_co2 = {
    "x": "datetime",
    "y[1]": "CO2",
    "color[1]": "blue",
    "type[1]": "line"
}

property_chart_TVOC = {
    "x": "datetime",
    "y[1]": "TVOC",
    "color[1]": "blue",
    "type[1]": "line"
}

property_chart_co = {
    "x": "datetime",
    "y[1]": "CO",
    "color[1]": "blue",
    "type[1]": "line"
}

property_chart_dp = {
    "x": "datetime",
    "y[1]": "DewPoint",
    "color[1]": "blue",
    "type[1]": "line"
}

property_chart_IA = {
    "x": "datetime",
    "y[1]": "IN_A",
    "color[1]": "blue",
    "type[1]": "line"
}

property_chart_IB = {
    "x": "datetime",
    "y[1]": "IN_B",
    "color[1]": "blue",
    "type[1]": "line"
}

property_chart_IC = {
    "x": "datetime",
    "y[1]": "IN_C",
    "color[1]": "blue",
    "type[1]": "line"
}

property_chart_IAvg = {
    "x": "datetime",
    "y[1]": "IN_Avg",
    "color[1]": "blue",
    "type[1]": "line"
}

# 節點資料
front_door_fan_0 = "OFF"
front_door_fan_1 = "OFF"
back_door_fan_0 = "OFF"
back_door_fan_1 = "OFF"
meeting_room_fan = "OFF"
AC_status = "OFF"

front_door_data = {}
back_door_data = {}
first_meeting_room_data = {}
second_meeting_room_data = {}
dl303_data = {}
power_box_data = {}
engine_room_data = {}

# 設定
with open("configs.json", "r") as f:
    setting = json.load(f)["SETTING"]
co2_upper_limit = setting["CO2_UPPER_LIMIT"]
turn_off_fan_time = setting["TURN_OFF_FAN_TIME"]
mr_co2_upper_limit = setting["MR_CO2_UPPER_LIMIT"]
mr_turn_off_fan_time = setting["MR_TURN_OFF_FAN_TIME"]
tc_upper_limit = setting["TC_UPPER_LIMIT"]
tc_lower_limit = setting["TC_LOWER_LIMIT"]
turn_off_ac_time = setting["TURN_OFF_AC_TIEM"]

# MQTT
client = connect(MQTT_IP, MQTT_PORT)

# APScheduler
task = None

# Web GUI
state_id_list = ['20240122161119098262-0.9642635253329301']

def on_init(state: State):
    state_id = get_state_id(state)
    if (state_id := get_state_id(state)) is not None and state_id != "":
        state_id_list.append(state_id)
    data_update(state, "2706/IAQ/2", pd.read_csv("csv/2706-IAQ-2.csv"))
    data_update(state, "2706/IAQ/1", pd.read_csv("csv/2706-IAQ-1.csv"))
    data_update(state, "2706/MeetingRoom/1", pd.read_csv("csv/2706-MeetingRoom-1.csv"))
    data_update(state, "2706/MeetingRoom/2", pd.read_csv("csv/2706-MeetingRoom-2.csv"))
    data_update(state, "DL303/Info", pd.read_csv("csv/DL303.csv"))

# 節點風扇狀態改變
def fan_state_change(state: State, var_name, value):
    if var_name == "front_door_fan_0":
        client.publish("2706/IAQ/2/control", json.dumps({"fan_0": value, "fan_1": state.front_door_fan_1}))
    elif var_name == "front_door_fan_1":
        client.publish("2706/IAQ/2/control", json.dumps({"fan_0": state.front_door_fan_0, "fan_1": value}))
    elif var_name == "back_door_fan_0":
        client.publish("2706/IAQ/1/control", json.dumps({"fan_0": value, "fan_1": state.back_door_fan_1}))
    elif var_name == "back_door_fan_1":
        client.publish("2706/IAQ/1/control", json.dumps({"fan_0": state.back_door_fan_0, "fan_1": value}))
    elif var_name == "meeting_room_fan":
        client.publish("2706/IAQ/3/control", json.dumps({"fan_0": value}))

# 節點空調狀態改變
def AC_status_change(state: State, var_name, value):
    if var_name == "AC_status":
        client.publish("2706/Air_Condiction/A/switch", json.dumps({"Status": value}))

# APScheduler任務更新
def update_tasks():
    global task, turn_off_ac_time, turn_off_fan_time, mr_turn_off_fan_time
    if task:
        task.shutdown()
        task.remove_all_jobs()
    task = BackgroundScheduler(timezone="Asia/Taipei")
    task.add_job(get_data, "interval", seconds=1, args=(gui, state_id_list))
    task.add_job(scheduled_tasks, "cron", hour=turn_off_fan_time, args=("2706",))
    task.add_job(scheduled_tasks, "cron", hour=mr_turn_off_fan_time, args=("Meeting",))
    task.add_job(scheduled_tasks, "cron", hour=turn_off_ac_time, args=("AC",))
    task.add_job(conditional_judgment, "interval", minutes=1)
    task.start()

# 設定更新
def update_setting(state: State):
    global co2_upper_limit, turn_off_fan_time, mr_co2_upper_limit, mr_turn_off_fan_time, tc_upper_limit, tc_lower_limit, turn_off_ac_time
    if int(state.turn_off_fan_time) < 24 and int(state.turn_off_fan_time) > 0:
        turn_off_fan_time = int(state.turn_off_fan_time)
    else:
        notify(state, "error", "請輸入正確的時間", True)
    if int(state.mr_turn_off_fan_time) < 24 and int(state.mr_turn_off_fan_time) > 0:
        mr_turn_off_fan_time = int(state.mr_turn_off_fan_time)
    else:
        notify(state, "error", "請輸入正確的時間", True)
    if int(state.turn_off_ac_time) < 24 and int(state.turn_off_ac_time > 0):
        turn_off_ac_time = int(state.turn_off_ac_time)
    else:
        notify(state, "error", "請輸入正確的時間", True)
    co2_upper_limit = state.co2_upper_limit
    mr_co2_upper_limit = state.mr_co2_upper_limit
    tc_upper_limit = state.tc_upper_limit
    tc_lower_limit = state.tc_lower_limit
    update_tasks()
    with open("configs.json", "w") as f:
        json.dump({
            "SETTING": {
                "CO2_UPPER_LIMIT": co2_upper_limit,
                "TURN_OFF_FAN_TIME": turn_off_fan_time,
                "MR_CO2_UPPER_LIMIT": mr_co2_upper_limit,
                "MR_TURN_OFF_FAN_TIME": mr_turn_off_fan_time,
                "TC_UPPER_LIMIT": tc_upper_limit,
                "TC_LOWER_LIMIT": tc_lower_limit,
                "TURN_OFF_AC_TIEM": turn_off_ac_time
            }
        }, f)

# 節點資料更新
def data_update(state: State, topic , data):
    # print(f"app.py: {topic} - {data}")
    if topic == "2706/IAQ/2":
        state.front_door_fan_0 = data["fan_0"].iloc[-1]
        state.front_door_fan_1 = data["fan_1"].iloc[-1]
        state.front_door_data["datetime"] = list(data["datetime"].iloc[-60:])
        state.front_door_data["Temperature"] = list(data["Temperature"].iloc[-60:])
        state.front_door_data["Humidity"] = list(data["Humidity"].iloc[-60:])
        state.front_door_data["CO2"] = list(data["CO2"].iloc[-60:])
        state.front_door_data["TVOC"] = list(data["TVOC"].iloc[-60:])
    elif topic == "2706/IAQ/1":
        state.back_door_fan_0 = data["fan_0"].iloc[-1]
        state.back_door_fan_1 = data["fan_1"].iloc[-1]
        state.back_door_data["datetime"] = list(data["datetime"].iloc[-60:])
        state.back_door_data["Temperature"] = list(data["Temperature"].iloc[-60:])
        state.back_door_data["Humidity"] = list(data["Humidity"].iloc[-60:])
        state.back_door_data["CO2"] = list(data["CO2"].iloc[-60:])
        state.back_door_data["TVOC"] = list(data["TVOC"].iloc[-60:])
    elif topic == "2706/MeetingRoom/1":
        state.meeting_room_fan = pd.read_csv("csv/2706-IAQ-3.csv")["fan_0"].iloc[-1]
        state.first_meeting_room_data["datetime"] = list(data["datetime"].iloc[-60:])
        state.first_meeting_room_data["Temperature"] = list(data["Temperature"].iloc[-60:])
        state.first_meeting_room_data["Humidity"] = list(data["Humidity"].iloc[-60:])
        state.first_meeting_room_data["CO2"] = list(data["CO2"].iloc[-60:])
        state.first_meeting_room_data["TVOC"] = list(data["TVOC"].iloc[-60:])
    elif topic == "2706/MeetingRoom/2":
        state.second_meeting_room_data["datetime"] = list(data["datetime"].iloc[-60:])
        state.second_meeting_room_data["Temperature"] = list(data["Temperature"].iloc[-60:])
        state.second_meeting_room_data["Humidity"] = list(data["Humidity"].iloc[-60:])
        state.second_meeting_room_data["CO2"] = list(data["CO2"].iloc[-60:])
        state.second_meeting_room_data["TVOC"] = list(data["TVOC"].iloc[-60:])
    elif topic == "DL303/Info":
        state.dl303_data["datetime"] = list(data["datetime"].iloc[-60:])
        state.dl303_data["Temperature"] = list(data["TemperatureC"].iloc[-60:])
        state.dl303_data["DewPoint"] = list(data["DewPointC"].iloc[-60:])
        state.dl303_data["Humidity"] = list(data["Humidity"].iloc[-60:])
        state.dl303_data["CO"] = list(data["CO"].iloc[-60:])
        state.dl303_data["CO2"] = list(data["CO2"].iloc[-60:])
    elif topic == "2706/PowerBox":
        state.power_box_data["datetime"] = list(data["datetime"].iloc[-60:])
        state.power_box_data["IN_A"] = list(data["IN_A"].iloc[-60:])
        state.power_box_data["IN_B"] = list(data["IN_B"].iloc[-60:])
        state.power_box_data["IN_C"] = list(data["IN_C"].iloc[-60:])
        state.power_box_data["IN_Avg"] = list(data["IN_Avg"].iloc[-60:])
    elif topic == "2706/Air_Condiction/A":
        state.AC_status = pd.read_csv("csv/2706-Air_Condiction-A-status.csv")['Status'].iloc[-1]
        state.engine_room_data["datetime"] = list(data["datetime"].iloc[-60:])
        state.engine_room_data["Temperature"] = list(data["Temperature"].iloc[-60:])
        state.engine_room_data["Humidity"] = list(data["Humidity"].iloc[-60:])

# 取得資料
def get_data(gui: Gui, state_id_list: list):
    invoke_callback(
        gui,
        state_id_list[0],
        data_update,
        ["2706/IAQ/2", pd.read_csv("csv/2706-IAQ-2.csv")]
    )
    invoke_callback(
        gui,
        state_id_list[0],
        data_update,
        ["2706/IAQ/1", pd.read_csv("csv/2706-IAQ-1.csv")]
        )
    invoke_callback(
        gui,
        state_id_list[0],
        data_update,
        ["2706/MeetingRoom/1", pd.read_csv("csv/2706-MeetingRoom-1.csv")]
    )
    invoke_callback(
        gui,
        state_id_list[0],
        data_update,
        ["2706/MeetingRoom/2", pd.read_csv("csv/2706-MeetingRoom-2.csv")]
    )
    invoke_callback(
        gui,
        state_id_list[0],
        data_update,
        ["DL303/Info", pd.read_csv("csv/DL303.csv")]
    )
    invoke_callback(
        gui,
        state_id_list[0],
        data_update,
        ["2706/PowerBox", pd.read_csv("csv/2706-PowerBox.csv")]
    )
    invoke_callback(
        gui,
        state_id_list[0],
        data_update,
        ["2706/Air_Condiction/A", pd.read_csv("csv/2706-Air_Condiction-A.csv")]
    )

def scheduled_tasks(loc: str):
    if loc == "2706":
        client.publish("2706/IAQ/1/control", json.dumps({"fan_0": "OFF", "fan_1": "OFF"}))
        client.publish("2706/IAQ/2/control", json.dumps({"fan_0": "OFF", "fan_1": "OFF"}))
    elif loc == "Meeting":
        client.publish("2706/IAQ/3/control", json.dumps({"fan_0": "OFF"}))
    elif loc == "AC":
        client.publish("2706/Air_Condiction/A/switch", json.dumps({"Status": "Off"}))  # ??

def conditional_judgment():
    if front_door_data["CO2"][-1] > co2_upper_limit or back_door_data["CO2"][-1] > co2_upper_limit:
        if datetime.now().hour >= 10 and datetime.now().hour < turn_off_fan_time:
            if pd.read_csv("csv/2706-IAQ-2.csv")["fan_0"].iloc[-1] == "OFF" or pd.read_csv("csv/2706-IAQ-2.csv")["fan_1"].iloc[-1] == "OFF":
                client.publish("2706/IAQ/2/control", json.dumps({"fan_0": "IN", "fan_1": "IN"}))
            if pd.read_csv("csv/2706-IAQ-1.csv")["fan_0"].iloc[-1] == "OFF" or pd.read_csv("csv/2706-IAQ-1.csv")["fan_1"].iloc[-1] == "OFF":
                client.publish("2706/IAQ/1/control", json.dumps({"fan_0": "OUT", "fan_1": "OUT"}))
    if first_meeting_room_data["CO2"][-1] > mr_co2_upper_limit:
        if datetime.now().hour >= 10 and datetime.now().hour < mr_turn_off_fan_time:
            if pd.read_csv("csv/2706-IAQ-3.csv")["fan_0"].iloc[-1] == "OFF":
                client.publish("2706/IAQ/3/control", json.dumps({"fan_0": "OUT"}))

# GUI
root_page = """
<|navbar|>
"""
Imac2706_pg = Markdown("pages/IMAC2706.md")
MeetingRoom_pg = Markdown("pages/MeetingRoom.md")
DL303_pg = Markdown("pages/DL303.md")
EngineRoom_pg = Markdown("pages/EngineRoom.md")
ElectricalBox_pg = Markdown("pages/ElectricalBox.md")
UPS_pg = Markdown("pages/UPS.md")
Configs_pg = Markdown("pages/Configs.md", endcoding="utf-8")

pages = {
    "/": root_page,
    "IMAC2706": Imac2706_pg,
    "MeetingRoom": MeetingRoom_pg,
    "DL303": DL303_pg,
    "EngineRoom": EngineRoom_pg,
    "ElectricalBox": ElectricalBox_pg,
    # "UPS": UPS_pg,
    "Config": Configs_pg,
}

if __name__ == "__main__":
    gui = Gui(pages=pages)
    update_tasks()
    gui.run(
        run_browser=False, 
        host="0.0.0.0", 
        port=5000, 
        debug=False, 
        title="NUTC IMAC",
        single_client=True
    )
