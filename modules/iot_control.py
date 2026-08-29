"""
modules/iot_control.py
=======================================================
Home / IoT Control
=======================================================
- Lights
- Fans
- Smart plugs
- Cameras
- Sensors
- Thermostats

Implemented over MQTT, the de-facto standard for smart-home
messaging (works with Home Assistant, Tasmota, ESPHome, Zigbee2MQTT
bridges, etc). If no broker is reachable, calls are safely mocked
and logged so the rest of the UI keeps working in a demo/dev setup.
"""

from config import Config
from utils.logger import get_logger

logger = get_logger("jarvis.iot")

_devices_state = {}  # in-memory fallback/demo state store


def _publish(topic: str, payload: str) -> bool:
    try:
        import paho.mqtt.publish as publish
        publish.single(
            topic,
            payload=payload,
            hostname=Config.MQTT_BROKER,
            port=Config.MQTT_PORT,
            auth={"username": Config.MQTT_USER, "password": Config.MQTT_PASS}
            if Config.MQTT_USER else None,
        )
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"MQTT publish failed ({exc}); using in-memory mock instead.")
        return False


def set_device(device_id: str, state: str, topic_prefix: str = "jarvis/devices") -> dict:
    """Generic setter for lights / fans / plugs / thermostats.
    state examples: 'on', 'off', a brightness/temperature value, etc."""
    topic = f"{topic_prefix}/{device_id}/set"
    ok = _publish(topic, state)
    _devices_state[device_id] = state
    logger.info(f"IoT device '{device_id}' -> '{state}' (mqtt_ok={ok})")
    return {"device_id": device_id, "state": state, "mqtt_published": ok}


def get_device_state(device_id: str) -> dict:
    return {"device_id": device_id, "state": _devices_state.get(device_id, "unknown")}


def list_devices() -> dict:
    return dict(_devices_state)


# ---------- Convenience wrappers matching the reference feature list ----------
def light(device_id: str, on: bool):
    return set_device(device_id, "on" if on else "off")


def fan(device_id: str, on: bool, speed: int | None = None):
    return set_device(device_id, str(speed) if (on and speed) else ("on" if on else "off"))


def smart_plug(device_id: str, on: bool):
    return set_device(device_id, "on" if on else "off")


def thermostat(device_id: str, target_temp_c: float):
    return set_device(device_id, str(target_temp_c))


def camera_snapshot_url(device_id: str) -> str:
    """Return the RTSP/HTTP snapshot URL configured for a camera device
    (integrate with your NVR / camera's local API)."""
    return f"http://<camera-host>/{device_id}/snapshot.jpg"


def sensor_reading(device_id: str) -> dict:
    return get_device_state(device_id)
