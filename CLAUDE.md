
## SEN66 Driver — mp_sen66
- Repo: https://github.com/DFgates/mp_sen66
- Fork of: https://github.com/ddland/mp_sen66
- Sensirion official drivers: 
- All PRs merged — driver is complete and production ready
- Key fixes applied:
  - Signed integer parsing (humidity, temperature, VOC, NOx)
  - CRC validation on get_data_ready
  - Idempotent start()/stop()
  - clean() uses self.stop()/self.start() — safe from any mode
  - set_sensor_altitude(85) called at startup
  - get_data() returns dict not tuple
  - Module docstring before imports
  - Class-level mutable attributes moved to __init__
  - Public reset() method added
  - device_reset mode changed to 'both'

## MicroPython Constraints — Always Check
- No `raise Error` — use `raise Exception`
- No `threading` — use `_thread` or single-threaded design
- No `struct.pack` format strings with `>` on all builds — test first
- `machine.SoftI2C` preferred over `machine.I2C` for XIAO ESP32-S3
- No pip — libraries are single .py files copied directly to device
- `urequests` not `requests` for HTTP
- `time.sleep()` not `asyncio` for delays
- WebREPL available but OTA via ESPHome preferred for display

## Secrets Handling
- `secrets.py` — gitignored everywhere, never committed
- `secrets.py.example` — committed as template
- Pattern applied in both garden-monitor/ and sen66-monitor/
- API keys live on Pi/Mac only — never on microcontrollers

## Flask Endpoint (not yet built)
- POST /air — receives SEN66 JSON, logs to SQLite with timestamp
- POST /garden — receives soil moisture JSON (future)
- GET / — serves unified dashboard
- Hourly LLM call to Chutes.ai with last 10 readings

## Pi (future)
- Already running
- Will add Flask + SQLite for sensor logging
- SD card wear concern — consider Samsung Pro Endurance or USB SSD
- API keys live here, not on microcontrollers

## Coding Conventions
- Verify file contents after every PR — paste actual file, not just summary
- secrets.py always gitignored before first commit in any new directory
- Commit messages are descriptive and lowercase
- One PR per logical change — small, reviewable, sequential
- Always confirm hardware pin numbers against actual board revision on arrival

## Pending Hardware Actions
- XIAO + SEN66 arrive → wire per pinout, flash MicroPython, copy sen66.py
  and main.py, test get_data() in REPL first before running main loop
- Try machine.I2C(0,...) first, fall back to SoftI2C if needed
- reTerminal E1002 arrives → flash ESPHome via USB-C, configure YAML dashboard

## Key URLs
- Garden Monitor dashboard: 
- GitHub: https://github.com/DFgates/
- SEN66 driver: https://github.com/DFgates/mp_sen66
- MicroPython firmware: https://micropython.org/download/ESP32_GENERIC/
- Chutes.ai API: https://api.chutes.ai/v1
- ESPHome web flasher: https://web.esphome.io
