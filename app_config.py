APP_SOFTWARE_MODEL_REV = "605001C4"

DATA_DIR_NAME = "Data_Files"
STARTUP_JSON_NAME = "startup.json"
UI_SCREEN1_FILE = "RC_page1b.ui"
UI_SCREEN2_FILE = "RC_Setup_Page_2.ui"

DEFAULT_TREE_FILE_NAME = "Test"

COLOR_ACTIVE = "pale green"
COLOR_INACTIVE = "grey94"
COLOR_DEFAULT = "white"

# Pico telemetry serial (USB-A host ports → Pico).
SERIAL_BAUDRATE = 115200
SERIAL_WINDOWS_PORT = "COM8"
SERIAL_LINUX_PORT = "/dev/ttyUSB0"
SERIAL_INIT_SLEEP_SEC = 0.2
SERIAL_DEINIT_SLEEP_SEC = 0.3
SERIAL_TICK_SLEEP_SEC = 0.25
POS_STALE_SEC = 2.0
DIA_STALE_SEC = 2.0

# USB CDC ACM gadget (Pi USB-C OTG → PC COM port) for Bass-320 Excel VBA transfer.
# Replaces the former Bluetooth-HID-as-keyboard transfer path (deprecated).
USB_COM_DEVICE = "/dev/ttyGS0"
USB_COM_BAUDRATE = 115200
USB_COM_OPEN_RETRY_SEC = 1.0
USB_TRANSFER_ENABLED_DEFAULT = False
USB_TRANSFER_CONNECTED_DEFAULT = False

# Wi-Fi HTTP Excel transfer (same Bass-320 payload as USB COM).
WIFI_HTTP_HOST = "0.0.0.0"
WIFI_HTTP_PORT = 8765
WIFI_TRANSFER_ENABLED_DEFAULT = False
WIFI_TRANSFER_CONNECTED_DEFAULT = False

# Deprecated: Bluetooth HID keyboard emulator was previously used to type into Excel.
# Do not enable for normal product boot — it conflicts with physical BT keyboards.
BT_HID_TRANSFER_DEPRECATED = True
BT_HID_ENABLED = False
BT_HID_DEVICE_NAME = "Recurve-Transfer"
BT_HID_HCI = 0
BT_HID_KEY_DELAY_SEC = 0.003

MODE_LOAD = 0
MODE_AUTO = 1
MODE_MANUAL = 2
