# Sensirion SEN66
Micropython driver for the sensirion SEN66 sensing platform.

## Installation
Copy the sen66.py to the library folder on the raspberrypi-pico (or just in the root of the device).

Connect the SEN66 to a I2C bus on the raspberrypi-pico and power it with the 3.3V source.
Once connected and started the `get_data()` command will start a new measurement and return the values as a dict, or `None` if data is not ready or a CRC error occurs. The dict has the following keys:

| Key | Description | Unit |
|---|---|---|
| `pm1p0` | Particulate matter 1.0 µm | µg/m³ |
| `pm2p5` | Particulate matter 2.5 µm | µg/m³ |
| `pm4p0` | Particulate matter 4.0 µm | µg/m³ |
| `pm10p0` | Particulate matter 10.0 µm | µg/m³ |
| `humidity` | Ambient relative humidity | % RH |
| `temperature` | Ambient temperature | °C |
| `voc` | VOC index | — |
| `nox` | NOx index | — |
| `co2` | CO₂ concentration | ppm |

If there has been enough time (somewhere between one and 2 days) since the last fan-cleaning routine, the fan will run 10 seconds at high power to flush some air through the system.

```python
from sen66 import SEN66
i2c0 = machine.I2C(0, sda=machine.Pin(0), scl=machine.Pin(1), freq=100000)
sen = SEN66(i2c0, altitude=85)  # altitude in meters above sea level (default 85 m, Arlington VA)
sen.start()
for ii in range(5):
    data = sen.get_data()
    if data:
        print("Temperature: {temperature}, Humidity: {humidity}, PM2.5: {pm2p5}, CO2: {co2}".format(**data))
    time.sleep(1)
```

If the watch-dog timer is used, a WDT object can be passed to the SEN66 initializing function and every second orso the watchdog is fed with an update.

## First-Time Startup

1. **Upload** `sen66.py` to the ESP32 root filesystem.
2. **Connect via REPL** and run the `__main__` block to verify I2C and readings:
   ```
   mpremote connect /dev/cu.usbserial-0001 run sen66.py
   ```
3. **First-ever power-on**: The VOC and NOx algorithms need approximately 24 hours of continuous operation to fully condition. During this period readings will drift — this is normal. After the initial conditioning, they stabilize within minutes of each restart.
4. **CO2 readings** improve over the first hour of operation as the sensor's internal algorithm warms up.
5. **Fan cleaning**: Consider running `sen.clean(force=True)` on the first run to flush the sensor. The driver handles periodic fan cleaning automatically after that (randomized 1–2 day interval).
6. **Data readiness**: After calling `sen.start()`, the sensor needs roughly 1 second before `get_data()` returns non-`None` values. The first few readings may show `0` or `0xFFFF` for some fields — wait 15–30 seconds for stable output.
