import json
import sys
from datetime import timedelta

import paho.mqtt.client as mqtt
from apscheduler.schedulers.background import BackgroundScheduler
from configs import *
from models import (
    DL303,
    ACSwitchLog,
    AirConditioner,
    BackDoor2706,
    FirstMeetingRoom,
    FrontDoor2706,
    PowerBox220V,
    SecondMeetingRoom,
    ServerRoom,
)

# 折線圖X/Y軸屬性
from property_chart import *
from sqlalchemy import Float, cast, desc, select
from sqlalchemy.orm import Session
from taipy.gui import Gui, Markdown, Page, State, get_state_id, invoke_callback, notify

front_door_fan_0 = "OFF"
front_door_fan_1 = "OFF"
back_door_fan_0 = "OFF"
back_door_fan_1 = "OFF"
meeting_room_fan = "OFF"
AC_status = "OFF"

# 節點資料
front_door_data = {
    "datetime": [""] * 60,
    "Temperature": [0] * 60,
    "Humidity": [0] * 60,
    "CO2": [0] * 60,
    "TVOC": [0] * 60,
    "fan_0": "False",
    "fan_1": "False",
}
back_door_data = {
    "datetime": [""] * 60,
    "Temperature": [0] * 60,
    "Humidity": [0] * 60,
    "CO2": [0] * 60,
    "TVOC": [0] * 60,
    "fan_0": "False",
    "fan_1": "False",
}
first_meeting_room_data = {
    "datetime": [""] * 60,
    "Temperature": [0] * 60,
    "Humidity": [0] * 60,
    "CO2": [0] * 60,
    "TVOC": [0] * 60,
}
second_meeting_room_data = {
    "datetime": [""] * 60,
    "Temperature": [0] * 60,
    "Humidity": [0] * 60,
    "CO2": [0] * 60,
    "TVOC": [0] * 60,
}
dl303_data = {
    "datetime": [""] * 60,
    "Temperature": [0] * 60,
    "DewPoint": [0] * 60,
    "Humidity": [0] * 60,
    "CO2": [0] * 60,
}
power_box_data = {
    "datetime": [""] * 60,
    "IN_A": [0] * 60,
    "IN_B": [0] * 60,
    "IN_C": [0] * 60,
    "IN_Avg": [0] * 60,
}
engine_room_data = {
    "datetime": [""] * 60,
    "Temperature": [0] * 60,
    "Humidity": [0] * 60,
    "AC_switch_log": [""] * 60,
    "AC_status": "OFF",
}


# 設定
with open("configs.json") as f:
    setting = json.load(f)["SETTING"]

co2_upper_limit = setting["CO2_UPPER_LIMIT"]
turn_off_fan_time = setting["TURN_OFF_FAN_TIME"]
mr_co2_upper_limit = setting["MR_CO2_UPPER_LIMIT"]
mr_turn_off_fan_time = setting["MR_TURN_OFF_FAN_TIME"]
tc_upper_limit = setting["TC_UPPER_LIMIT"]
tc_lower_limit = setting["TC_LOWER_LIMIT"]
turn_off_ac_time = setting["TURN_OFF_AC_TIEM"]

# MQTT
client = mqtt.Client()
client.connect(MQTT_IP, MQTT_PORT)


def mqtt_on_disconnect(client, userdata, rc):
    print("==============Disconnected==============")
    client.loop_start()


client.on_disconnect = mqtt_on_disconnect
client.loop_start()

# APScheduler
task = None

# Web GUI
state_id_list = ["20240122161119098262-0.9642635253329301"]


def on_init(state: State):
    state_id = get_state_id(state)
    if (state_id := get_state_id(state)) is not None and state_id != "":
        state_id_list.append(state_id)

    print("===============init===============")

    data_update(state, "2706/IAQ/2", front_door_data)
    data_update(state, "2706/IAQ/1", back_door_data)
    data_update(state, "2706/MeetingRoom/1", first_meeting_room_data)
    data_update(state, "2706/MeetingRoom/2", second_meeting_room_data)
    data_update(state, "DL303/Info", dl303_data)

    print("===============init_complete===============")


def fan_state_change(state: State, var_name: str, value: str):
    """節點風扇狀態改變

    Args:
        state (State): Taipy的State物件, 用來存放狀態
        var_name (str): 變數名稱，用來判斷是哪個風扇
        value (str): 風扇狀態(ON/OFF)

    """
    if var_name == "front_door_fan_0":
        client.publish(
            "2706/IAQ/2/control",
            json.dumps({"fan_0": value, "fan_1": state.front_door_fan_1}),
        )
    elif var_name == "front_door_fan_1":
        client.publish(
            "2706/IAQ/2/control",
            json.dumps({"fan_0": state.front_door_fan_0, "fan_1": value}),
        )
    elif var_name == "back_door_fan_0":
        client.publish(
            "2706/IAQ/1/control",
            json.dumps({"fan_0": value, "fan_1": state.back_door_fan_1}),
        )
    elif var_name == "back_door_fan_1":
        client.publish(
            "2706/IAQ/1/control",
            json.dumps({"fan_0": state.back_door_fan_0, "fan_1": value}),
        )
    elif var_name == "meeting_room_fan":
        client.publish("2706/IAQ/3/control", json.dumps({"fan_0": value}))


def AC_status_change(state: State, var_name: str, value: str):
    """節點空調狀態改變

    Args:
        state (State): Taipy的State物件, 用來存放狀態
        var_name (str): 變數名稱，用來判斷是哪個空調
        value (str): 空調狀態(ON/OFF)

    """
    if var_name == "AC_status":
        client.publish("2706/Air_Condiction/A/control", json.dumps({"Status": value}))


def update_tasks():
    """更新APScheduler任務
    如果目前已經存在task物件，則先完全關閉task，並重新建立新的task物件並加入任務
    """
    global task, turn_off_ac_time, turn_off_fan_time, mr_turn_off_fan_time
    if task:
        task.shutdown()
        task.remove_all_jobs()
    task = BackgroundScheduler(timezone="Asia/Taipei")
    task.add_job(get_data, "interval", seconds=10, args=(gui, state_id_list))
    task.add_job(shutdown_fan_and_AC, "cron", hour=turn_off_fan_time, args=("2706",))
    task.add_job(shutdown_fan_and_AC, "cron", hour=mr_turn_off_fan_time, args=("Meeting",))
    task.add_job(shutdown_fan_and_AC, "cron", hour=turn_off_ac_time, args=("AC",))
    task.start()


def validate_time(state: State, hour: int):
    """驗證風扇時間是否正確(0 < hour < 24)"""
    if hour < 24 and hour > 0:
        return True

    notify(state, "error", "請輸入正確的時間", True)
    return False


# 設定更新
def update_setting(state: State):
    """更新Taipy顯示設定"""
    global \
        co2_upper_limit, \
        turn_off_fan_time, \
        mr_co2_upper_limit, \
        mr_turn_off_fan_time, \
        tc_upper_limit, \
        tc_lower_limit, \
        turn_off_ac_time

    if validate_time(state, int(state.turn_off_fan_time)):
        turn_off_fan_time = int(state.turn_off_fan_time)

    if validate_time(state, int(state.mr_turn_off_fan_time)):
        mr_turn_off_fan_time = int(state.mr_turn_off_fan_time)

    if validate_time(state, int(state.turn_off_ac_time)):
        turn_off_ac_time = int(state.turn_off_ac_time)

    co2_upper_limit = state.co2_upper_limit
    mr_co2_upper_limit = state.mr_co2_upper_limit
    tc_upper_limit = state.tc_upper_limit
    tc_lower_limit = state.tc_lower_limit
    update_tasks()

    with open("configs.json", "w") as f:
        json.dump(
            {
                "SETTING": {
                    "CO2_UPPER_LIMIT": co2_upper_limit,
                    "TURN_OFF_FAN_TIME": turn_off_fan_time,
                    "MR_CO2_UPPER_LIMIT": mr_co2_upper_limit,
                    "MR_TURN_OFF_FAN_TIME": mr_turn_off_fan_time,
                    "TC_UPPER_LIMIT": tc_upper_limit,
                    "TC_LOWER_LIMIT": tc_lower_limit,
                    "TURN_OFF_AC_TIEM": turn_off_ac_time,
                }
            },
            f,
        )


def data_update(state: State, topic: str, data: dict):
    """將節點資料更新到Taipy的State物件以顯示在GUI上

    Topic:
        - 2706/IAQ/2: 前門
        - 2706/IAQ/1: 後門
        - 2706/MeetingRoom/1: 會議室1
        - 2706/MeetingRoom/2: 會議室2
        - DL303/Info: DL303
        - 2706/PowerBox: 電箱
        - 2706/Air_Condiction/A: 空調

    Args:
        state (State): Taipy的State物件, 用來存放狀態
        topic (str): 資料
        data (dict): 資料內容

    """
    if topic == "2706/IAQ/2":
        state.front_door_fan_0 = data["fan_0"]
        state.front_door_fan_1 = data["fan_1"]
        state.front_door_data["datetime"] = data["datetime"]
        state.front_door_data["Temperature"] = data["Temperature"]
        state.front_door_data["Humidity"] = data["Humidity"]
        state.front_door_data["CO2"] = data["CO2"]
        state.front_door_data["TVOC"] = data["TVOC"]

    elif topic == "2706/IAQ/1":
        state.back_door_fan_0 = data["fan_0"]
        state.back_door_fan_1 = data["fan_1"]
        state.back_door_data["datetime"] = data["datetime"]
        state.back_door_data["Temperature"] = data["Temperature"]
        state.back_door_data["Humidity"] = data["Humidity"]
        state.back_door_data["CO2"] = data["CO2"]
        state.back_door_data["TVOC"] = data["TVOC"]

    elif topic == "2706/MeetingRoom/1":
        state.meeting_room_fan = "OFF"  # 目前風扇已移除
        state.first_meeting_room_data["datetime"] = data["datetime"]
        state.first_meeting_room_data["Temperature"] = data["Temperature"]
        state.first_meeting_room_data["Humidity"] = data["Humidity"]
        state.first_meeting_room_data["CO2"] = data["CO2"]
        state.first_meeting_room_data["TVOC"] = data["TVOC"]

    elif topic == "2706/MeetingRoom/2":
        state.second_meeting_room_data["datetime"] = data["datetime"]
        state.second_meeting_room_data["Temperature"] = data["Temperature"]
        state.second_meeting_room_data["Humidity"] = data["Humidity"]
        state.second_meeting_room_data["CO2"] = data["CO2"]
        state.second_meeting_room_data["TVOC"] = data["TVOC"]

    elif topic == "DL303/Info":
        state.dl303_data["datetime"] = data["datetime"]
        state.dl303_data["Temperature"] = data["Temperature"]
        state.dl303_data["DewPoint"] = data["DewPoint"]
        state.dl303_data["Humidity"] = data["Humidity"]
        state.dl303_data["CO2"] = data["CO2"]

    elif topic == "2706/PowerBox":
        state.power_box_data["datetime"] = data["datetime"]
        state.power_box_data["IN_A"] = data["IN_A"]
        state.power_box_data["IN_B"] = data["IN_B"]
        state.power_box_data["IN_C"] = data["IN_C"]
        state.power_box_data["IN_Avg"] = data["IN_Avg"]

    elif topic == "2706/Air_Condiction/A":
        state.AC_status = "ON" if data["AC_status"] else "OFF"
        state.engine_room_data["datetime"] = data["datetime"]
        state.engine_room_data["Temperature"] = data["Temperature"]
        state.engine_room_data["Humidity"] = data["Humidity"]
        state.engine_room_data["AC_switch_log"] = data["AC_switch_log"]


# 取得資料
def get_data(gui: Gui, state_id_list: list):  # 節點資料
    front_door_data = {
        "datetime": [],
        "Temperature": [],
        "Humidity": [],
        "CO2": [],
        "TVOC": [],
        "fan_0": "False",
        "fan_1": "False",
    }
    back_door_data = {
        "datetime": [],
        "Temperature": [],
        "Humidity": [],
        "CO2": [],
        "TVOC": [],
        "fan_0": "False",
        "fan_1": "False",
    }
    first_meeting_room_data = {
        "datetime": [],
        "Temperature": [],
        "Humidity": [],
        "CO2": [],
        "TVOC": [],
    }
    second_meeting_room_data = {
        "datetime": [],
        "Temperature": [],
        "Humidity": [],
        "CO2": [],
        "TVOC": [],
    }
    dl303_data = {
        "datetime": [],
        "Temperature": [],
        "DewPoint": [],
        "Humidity": [],
        "CO2": [],
    }
    power_box_data = {"datetime": [], "IN_A": [], "IN_B": [], "IN_C": [], "IN_Avg": []}
    engine_room_data = {
        "datetime": [],
        "Temperature": [],
        "Humidity": [],
        "AC_switch_log": [],
        "AC_status": "OFF",
    }
    with Session(engine) as session:
        IAQ_2_result = session.execute(
            select(
                cast(FrontDoor2706.temp, Float),
                cast(FrontDoor2706.humi, Float),
                cast(FrontDoor2706.co2, Float),
                cast(FrontDoor2706.tvoc, Float),
                FrontDoor2706.fan3,
                FrontDoor2706.fan4,
                FrontDoor2706.timestamp,
            )
            .order_by(desc(FrontDoor2706.timestamp))
            .limit(60)
        ).all()

        IAQ_1_result = session.execute(
            select(
                cast(BackDoor2706.temp, Float),
                cast(BackDoor2706.humi, Float),
                cast(BackDoor2706.co2, Float),
                cast(BackDoor2706.tvoc, Float),
                BackDoor2706.fan1,
                BackDoor2706.fan2,
                BackDoor2706.timestamp,
            )
            .order_by(desc(BackDoor2706.timestamp))
            .limit(60)
        ).all()

        first_meeting_room_result = session.execute(
            select(
                cast(FirstMeetingRoom.temp, Float),
                cast(FirstMeetingRoom.humi, Float),
                cast(FirstMeetingRoom.co2, Float),
                cast(FirstMeetingRoom.tvoc, Float),
                FirstMeetingRoom.timestamp,
            )
            .order_by(desc(FirstMeetingRoom.timestamp))
            .limit(60)
        ).all()

        second_meeting_room_result = session.execute(
            select(
                cast(SecondMeetingRoom.temp, Float),
                cast(SecondMeetingRoom.humi, Float),
                cast(SecondMeetingRoom.co2, Float),
                cast(SecondMeetingRoom.tvoc, Float),
                SecondMeetingRoom.timestamp,
            )
            .order_by(desc(SecondMeetingRoom.timestamp))
            .limit(60)
        ).all()

        dl303_result = session.execute(
            select(
                cast(DL303.temp, Float),
                cast(DL303.humi, Float),
                cast(DL303.dew_point, Float),  # 不知道是不是 CO
                cast(DL303.co2, Float),
                DL303.timestamp,
            )
            .order_by(desc(DL303.timestamp))
            .limit(60)
        ).all()

        power_box_result = session.execute(
            select(
                cast(PowerBox220V.in_a, Float),
                cast(PowerBox220V.in_b, Float),
                cast(PowerBox220V.in_c, Float),
                cast(PowerBox220V.in_avg, Float),
                PowerBox220V.timestamp,
            )
            .order_by(desc(PowerBox220V.timestamp))
            .limit(60)
        ).all()

        engine_room_result = session.execute(
            select(
                cast(ServerRoom.temp, Float),
                cast(ServerRoom.humi, Float),
                ServerRoom.timestamp,
            )
            .order_by(desc(ServerRoom.timestamp))
            .limit(60)
        ).all()

        ac_switch_log_result = session.execute(
            select(ACSwitchLog.status).order_by(desc(ACSwitchLog.timestamp)).limit(60)
        ).all()

        engine_room_data["AC_status"] = session.execute(
            select(ACSwitchLog.status).order_by(desc(ACSwitchLog.timestamp)).limit(1)
        ).all()[0][0]

    front_door_data["fan_0"] = IAQ_2_result[-1][4]
    front_door_data["fan_1"] = IAQ_2_result[-1][5]
    back_door_data["fan_0"] = IAQ_1_result[-1][4]
    back_door_data["fan_1"] = IAQ_1_result[-1][5]

    for index in range(len(engine_room_result)):
        # 轉換時區至台北(UTC+8)
        front_door_time = IAQ_2_result[index][6] + timedelta(hours=8)
        back_door_time = IAQ_1_result[index][6] + timedelta(hours=8)
        first_meeting_room_time = first_meeting_room_result[index][4] + timedelta(hours=8)
        second_meeting_room_time = second_meeting_room_result[index][4] + timedelta(hours=8)
        dl303_time = dl303_result[index][4] + timedelta(hours=8)
        power_box_time = power_box_result[index][4] + timedelta(hours=8)
        engine_room_time = engine_room_result[index][2] + timedelta(hours=8)

        # 更新資料
        front_door_data["Temperature"].append(IAQ_2_result[index][0])
        front_door_data["Humidity"].append(IAQ_2_result[index][1])
        front_door_data["CO2"].append(IAQ_2_result[index][2])
        front_door_data["TVOC"].append(IAQ_2_result[index][3])
        front_door_data["datetime"].append(front_door_time.strftime("%Y-%m-%d %H:%M:%S"))

        back_door_data["Temperature"].append(IAQ_1_result[index][0])
        back_door_data["Humidity"].append(IAQ_1_result[index][1])
        back_door_data["CO2"].append(IAQ_1_result[index][2])
        back_door_data["TVOC"].append(IAQ_1_result[index][3])
        back_door_data["datetime"].append(back_door_time.strftime("%Y-%m-%d %H:%M:%S"))

        first_meeting_room_data["Temperature"].append(first_meeting_room_result[index][0])
        first_meeting_room_data["Humidity"].append(first_meeting_room_result[index][1])
        first_meeting_room_data["CO2"].append(first_meeting_room_result[index][2])
        first_meeting_room_data["TVOC"].append(first_meeting_room_result[index][3])
        first_meeting_room_data["datetime"].append(
            first_meeting_room_time.strftime("%Y-%m-%d %H:%M:%S")
        )

        second_meeting_room_data["Temperature"].append(second_meeting_room_result[index][0])
        second_meeting_room_data["Humidity"].append(second_meeting_room_result[index][1])
        second_meeting_room_data["CO2"].append(second_meeting_room_result[index][2])
        second_meeting_room_data["TVOC"].append(second_meeting_room_result[index][3])
        second_meeting_room_data["datetime"].append(
            second_meeting_room_time.strftime("%Y-%m-%d %H:%M:%S")
        )

        dl303_data["Temperature"].append(dl303_result[index][0])
        dl303_data["Humidity"].append(dl303_result[index][1])
        dl303_data["DewPoint"].append(dl303_result[index][2])
        dl303_data["CO2"].append(dl303_result[index][3])
        dl303_data["datetime"].append(dl303_time.strftime("%Y-%m-%d %H:%M:%S"))

        power_box_data["IN_A"].append(power_box_result[index][0])
        power_box_data["IN_B"].append(power_box_result[index][1])
        power_box_data["IN_C"].append(power_box_result[index][2])
        power_box_data["IN_Avg"].append(power_box_result[index][3])
        power_box_data["datetime"].append(power_box_time.strftime("%Y-%m-%d %H:%M:%S"))

        engine_room_data["Temperature"].append(engine_room_result[index][0])
        engine_room_data["Humidity"].append(engine_room_result[index][1])
        engine_room_data["datetime"].append(engine_room_time.strftime("%Y-%m-%d %H:%M:%S"))
        engine_room_data["AC_switch_log"].append(ac_switch_log_result[index][0])

    invoke_callback(gui, state_id_list[0], data_update, ["2706/IAQ/2", front_door_data])
    invoke_callback(gui, state_id_list[0], data_update, ["2706/IAQ/1", back_door_data])
    invoke_callback(
        gui,
        state_id_list[0],
        data_update,
        ["2706/MeetingRoom/1", first_meeting_room_data],
    )
    invoke_callback(
        gui,
        state_id_list[0],
        data_update,
        ["2706/MeetingRoom/2", second_meeting_room_data],
    )
    invoke_callback(gui, state_id_list[0], data_update, ["DL303/Info", dl303_data])
    invoke_callback(gui, state_id_list[0], data_update, ["2706/PowerBox", power_box_data])
    invoke_callback(gui, state_id_list[0], data_update, ["2706/Air_Condiction/A", engine_room_data])


def shutdown_fan_and_AC(loc: str):
    """關閉風扇和空調
    當時間到達設定的時間時，將風扇和空調關閉

    Args:
        loc (str): 設施位置

    """
    if loc == "2706":
        client.publish("2706/IAQ/1/control", json.dumps({"fan_0": "OFF", "fan_1": "OFF"}))
        client.publish("2706/IAQ/2/control", json.dumps({"fan_0": "OFF", "fan_1": "OFF"}))
    elif loc == "Meeting":
        client.publish("2706/IAQ/3/control", json.dumps({"fan_0": "OFF"}))
    elif loc == "AC":
        client.publish("2706/Air_Condiction/A/switch", json.dumps({"Status": "Off"}))


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
    "Config": Configs_pg,
}

if __name__ == "__main__":
    gui = Gui(pages=pages)
    update_tasks()
    gui.run(
        run_browser=False,
        host=HOST,
        port=PORT,
        debug=False,
        title="NUTC IMAC",
        globals=globals(),
    )
