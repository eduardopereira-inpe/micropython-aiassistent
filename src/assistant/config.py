
from assistant.utils.dotenv import load_dotenv
from connectivity.wifi import connect_to_wifi



config = load_dotenv("env.txt")

API_KEY = config.get("API_KEY")
SSID = config.get("WIFI_SSID")
PASSWORD = config.get("WIFI_PASS")


connect_to_wifi(
    SSID,
    PASSWORD
)

print(f"WIFI-SSID {SSID}")