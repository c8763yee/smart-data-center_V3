from sqlalchemy import Engine, create_engine

__all__ = [
    "MQTT_IP",
    "MQTT_PORT",
    "HOST",
    "PORT",
    "DB_SERVER",
    "DB_NAME",
    "engine",
]

# MQTT Config
MQTT_IP: str = "127.0.0.1"
MQTT_PORT: int = 1883


# Flask config
HOST: str = "0.0.0.0"
PORT: int = 8000

# Database Config(MariaDB)
DB_SERVER: str = (  # 參考原本Server上的Config來修改<username>, <password>, <ip>, <port>)
    "mysql+pymysql://<username>:<password>@<ip>:<port>"
)
DB_NAME: str = "factory"
engine: Engine = create_engine(f"{DB_SERVER}/{DB_NAME}")
