import network
import urequests
import time
import machine
from sen66 import SEN66

# --- config ---
SSID        = 'your_ssid'
PASSWORD    = 'your_password'
PI_ENDPOINT = 'http://192.168.99.x:5000/air'  # update with your Pi's IP
INTERVAL    = 300  # 5 minutes
ALTITUDE    = 213  # Arlington, VA 22201

# --- hardware --- CHECK IF PIN 21 IS LED
led = machine.Pin(21, machine.Pin.OUT)  # XIAO ESP32-S3 onboard LED
i2c = machine.SoftI2C(sda=machine.Pin(5), scl=machine.Pin(6), freq=100000)

def led_error(n=3):
    """Flash LED n times to indicate error."""
    for _ in range(n):
        led.value(1)
        time.sleep(0.2)
        led.value(0)
        time.sleep(0.2)

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        return wlan
    wlan.connect(SSID, PASSWORD)
    for _ in range(20):
        if wlan.isconnected():
            print('WiFi connected:', wlan.ifconfig()[0])
            return wlan
        time.sleep(0.5)
    print('WiFi failed')
    led_error(5)
    return None

def post_data(data):
    try:
        r = urequests.post(PI_ENDPOINT, json=data, timeout=10)
        r.close()
        return True
    except Exception as e:
        print('POST failed:', e)
        led_error(3)
        return False

# --- startup ---
sen = SEN66(i2c, altitude=ALTITUDE)
sen.start()
print('Warming up sensor...')
time.sleep(15)

wlan = connect_wifi()

# --- main loop ---
while True:
    data = sen.get_data()
    if data is None:
        print('No data ready')
        led_error(2)
    else:
        print(data)
        if wlan and wlan.isconnected():
            post_data(data)
        else:
            print('WiFi down, reconnecting...')
            led_error(5)
            wlan = connect_wifi()
    time.sleep(INTERVAL)
