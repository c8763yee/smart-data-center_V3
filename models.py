# -*- coding: UTF-8 -*-
import datetime
import os

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    Column,
    Float,
    Integer,
    String,
)
from sqlalchemy.dialects.mysql import DECIMAL
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class BaseTable:
    __table_args__ = {"mysql_charset": "utf8mb4"}
    id = Column(Integer, nullable=False, primary_key=True)
    timestamp = Column(TIMESTAMP, nullable=False, default=datetime.datetime.utcnow())


class TestTable(BaseTable, Base):  # 測試用
    __tablename__ = "TestTable"
    tes = Column(Float(4, 0), nullable=False)
    tt = Column(Float(4, 1), nullable=False)
    te = Column(Float(4, 2), nullable=False)
    temp = Column(DECIMAL(5, 1), nullable=False)
    humi = Column(DECIMAL(5, 2), nullable=False)
    co2 = Column(DECIMAL(6, 1), nullable=False)


class FrontDoor2706(BaseTable, Base):  # 前門風扇，改fan_0,fan_1
    __tablename__ = "FrontDoor2706"
    temp = Column(Float(5, 2), nullable=False)
    humi = Column(Float(5, 2), nullable=False)
    co2 = Column(Float(6, 2), nullable=False)
    tvoc = Column(Float(6, 2), nullable=False)
    fan3 = Column(String(40), nullable=False)
    fan4 = Column(String(40), nullable=False)


class BackDoor2706(BaseTable, Base):  # 後門風扇
    __tablename__ = "BackDoor2706"
    temp = Column(Float(5, 2), nullable=False)
    humi = Column(Float(5, 2), nullable=False)
    co2 = Column(Float(6, 2), nullable=False)
    tvoc = Column(Float(6, 2), nullable=False)
    fan1 = Column(String(40), nullable=False)
    fan2 = Column(String(40), nullable=False)


class FirstMeetingRoomFun(BaseTable, Base):
    __tablename__ = "FirstMeetingRoomFun"
    fan0 = Column(String(40), nullable=False)


class FirstMeetingRoom(BaseTable, Base):  # 第一會議室
    __tablename__ = "FirstMeetingRoom"
    temp = Column(Float(5, 2), nullable=False)
    humi = Column(Float(5, 2), nullable=False)
    co2 = Column(Float(6, 2), nullable=False)
    tvoc = Column(Float(6, 2), nullable=False)


class SecondMeetingRoom(BaseTable, Base):  # 第二會議室
    __tablename__ = "SecondMeetingRoom"
    temp = Column(Float(5, 2), nullable=False)
    humi = Column(Float(5, 2), nullable=False)
    co2 = Column(Float(6, 2), nullable=False)
    tvoc = Column(Float(6, 2), nullable=False)


class PowerBox220V(BaseTable, Base):  # Power Box 220V
    __tablename__ = "Power_Box_220V"
    in_a = Column(Float(5, 2), nullable=False)
    in_b = Column(Float(5, 2), nullable=False)
    in_c = Column(Float(5, 2), nullable=False)
    in_avg = Column(Float(5, 2), nullable=False)
    kw_a = Column(Float(5, 2), nullable=False)
    kw_b = Column(Float(5, 2), nullable=False)
    kw_c = Column(Float(5, 2), nullable=False)
    kw_tot = Column(Float(5, 2), nullable=False)


class ServerRoom(BaseTable, Base):  # 機房
    __tablename__ = "ServerRoom"
    temp = Column(Float(5, 2), nullable=False)
    humi = Column(Float(5, 2), nullable=False)


class AirConditioner(BaseTable, Base):  # 冷氣狀態
    __tablename__ = "AirConditioner"
    status = Column(Boolean, nullable=False)


class ACSwitchLog(BaseTable, Base):  # 冷氣狀態Log
    __tablename__ = "ACSwitchLog"
    status = Column(Boolean, nullable=False)


class DL303(BaseTable, Base):
    __tablename__ = "DL303"
    temp = Column(Float(5, 2), nullable=False)
    humi = Column(Float(5, 2), nullable=False)
    dew_point = Column(Float(5, 2), nullable=False)
    co2 = Column(Float(6, 2), nullable=False)


class RotationUser(BaseTable, Base):
    __tablename__ = "RotationUser"
    user = Column(String(40), nullable=False)


class DailyReport(BaseTable, Base):
    __tablename__ = "DailyReport"
    PoP12h = Column(Integer, nullable=False)
    Wx = Column(String(40), nullable=False)
    AT = Column(Integer, nullable=False)
    CI = Column(String(40), nullable=False)
    PoP6h = Column(Integer, nullable=False)
    RH = Column(Integer, nullable=False)
    T = Column(Integer, nullable=False)
    Td = Column(Integer, nullable=False)
    WD = Column(String(40), nullable=False)
    WS = Column(Float, nullable=False)
    WeatherDescription = Column(String(255), nullable=False)


# class ET7044(BaseTable, Base):  # ET7044 開關
#     __tablename__ = "ET7044"
#     SW1 = Column(Boolean, nullable=False)
#     SW2 = Column(Boolean, nullable=False)
#     SW3 = Column(Boolean, nullable=False)
#     SW4 = Column(Boolean, nullable=False)
#     SW5 = Column(Boolean, nullable=False)
#     SW6 = Column(Boolean, nullable=False)
#     SW7 = Column(Boolean, nullable=False)
#     SW8 = Column(Boolean, nullable=False)


# class UPSA(BaseTable, Base):  # UPS A
#     __tablename__ = "UPS_A"
#     Device_Locate = Column(String(40), nullable=False)
#     Device_Life = Column(String(20), nullable=False)
#     Input_Line = Column(Integer, nullable=False)
#     Input_Volt = Column(Float(5, 2), nullable=False)
#     Input_Freq = Column(Float(5, 2), nullable=False)
#     Output_Line = Column(Integer, nullable=False)
#     Output_Freq = Column(Float(5, 2), nullable=False)
#     Output_Volt = Column(Float(5, 2), nullable=False)
#     Output_Amp = Column(Float(6, 4), nullable=False)
#     Output_Watt = Column(Float(5, 3), nullable=False)
#     Output_Percent = Column(Integer, nullable=False)
#     System_Mode = Column(String(20), nullable=False)
#     Battery_Volt = Column(Integer, nullable=False)
#     Battery_Remain_Percent = Column(Integer, nullable=False)
#     Battery_Health = Column(String(20), nullable=False)
#     Battery_Status = Column(String(20), nullable=False)
#     Battery_Charge_Mode = Column(String(40), nullable=False)
#     Battery_Temp = Column(Integer, nullable=False)
#     Battery_Last_Change_Year = Column(Integer, nullable=False)
#     Battery_Last_Change_Mon = Column(Integer, nullable=False)
#     Battery_Last_Change_Day = Column(Integer, nullable=False)
#     Battery_Next_Change_Year = Column(Integer, nullable=False)
#     Battery_Next_Change_Mon = Column(Integer, nullable=False)
#     Battery_Next_Change_Day = Column(Integer, nullable=False)


# class UPSB(BaseTable, Base):  # UPS B
#     __tablename__ = "UPS_B"
#     Device_Locate = Column(String(40), nullable=False)
#     Device_Life = Column(String(20), nullable=False)
#     Input_Line = Column(Integer, nullable=False)
#     Input_Volt = Column(Float(5, 2), nullable=False)
#     Input_Freq = Column(Float(5, 2), nullable=False)
#     Output_Line = Column(Integer, nullable=False)
#     Output_Freq = Column(Float(5, 2), nullable=False)
#     Output_Volt = Column(Float(5, 2), nullable=False)
#     Output_Amp = Column(Float(6, 4), nullable=False)
#     Output_Watt = Column(Float(5, 3), nullable=False)
#     Output_Percent = Column(Integer, nullable=False)
#     System_Mode = Column(String(20), nullable=False)
#     Battery_Volt = Column(Integer, nullable=False)
#     Battery_Remain_Percent = Column(Integer, nullable=False)
#     Battery_Health = Column(String(20), nullable=False)
#     Battery_Status = Column(String(20), nullable=False)
#     Battery_Charge_Mode = Column(String(40), nullable=False)
#     Battery_Temp = Column(Integer, nullable=False)
#     Battery_Last_Change_Year = Column(Integer, nullable=False)
#     Battery_Last_Change_Mon = Column(Integer, nullable=False)
#     Battery_Last_Change_Day = Column(Integer, nullable=False)
#     Battery_Next_Change_Year = Column(Integer, nullable=False)
#     Battery_Next_Change_Mon = Column(Integer, nullable=False)
#     Battery_Next_Change_Day = Column(Integer, nullable=False)


if __name__ == "__main__":
    # We no longer use dotenv to load environment variables.
    # Instead, we use configs.py to store the database connection string.
    if os.path.exists("configs.py") is False:
        raise FileNotFoundError(
            "Can't find configs.py, please create configs.py based on configs_simple.py"
        )

    from configs import engine

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    # Legacy code:
    # dotenv_path = f"{os.path.dirname(os.path.abspath(__file__))}/.env"
    # if os.path.exists(dotenv_path):
    #     load_dotenv(f"{os.path.dirname(os.path.abspath(__file__))}/.env")

    # engine = create_engine(os.environ.get("SQL_SERVER"), echo=True)
