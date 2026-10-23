import board
import busio
import digitalio
import time, rtc, wifi, socketpool, adafruit_ntp
import adafruit_dht
from grove_lcd import GroveLCD
import creds
import pwmio


def disp_time():
    now = time.localtime()
    lcd.write_line(0, f"{now.tm_year}-{now.tm_mon:02d}-{now.tm_mday:02d} ")
    lcd.write_line(1, f"{now.tm_hour:02d}:{now.tm_min:02d}:{now.tm_sec:02d}")


def disp_weather():
    try:
        temp = dht.temperature
        humity = dht.humidity
        lcd.write_line(0, f"Temp: {temp} C")
        lcd.write_line(1, f"Humidity: {humity} %")
    except RuntimeError as e:
        # DHT sensors often fail a read; just retry next loop
        print("DHT read error:", e)


def connect_wifi(ssid, password, attempts=5, timeout=10):
    print('Connecting to wifi AP...')
    for attempt in range(1, attempts + 1):
        try:
            if not wifi.radio.connected:
                wifi.radio.connect(ssid, password, timeout=timeout)
            print(f"connected to {ssid}, IP {wifi.radio.ipv4_address}")
            return True
        except Exception as e:
            print(f"attempt {attempt}/{attempts} failed: {e!r}")
            time.sleep(attempt * 2)
    return False

def button_pressed():
    """Return True once per press (falling edge), debounced."""
    global _last_level, _last_change
    level = button.value
    now = time.monotonic()
    if level != _last_level and now - _last_change > DEBOUNCE:
        _last_level = level
        _last_change = now
        return not level      # True only on press, not on release
    return False

def step(state):
    """Advance to the next menu on a button press, wrapping around."""
    if button_pressed():
        return (state + 1) % len(MENUS)
    return state

button = digitalio.DigitalInOut(board.GP17)
button.switch_to_input(pull=digitalio.Pull.UP)
#buzzer = digitalio.DigitalInOut(board.GP16)
#buzzer.switch_to_output()

MENUS = [disp_time, disp_weather]
DEBOUNCE = 0.05
_last_level = True
_last_change = 0.0
state = 0
last_state = None
last_draw = 0.0
BEEP_TIME = 0.2
beep_until = 0.0

led = digitalio.DigitalInOut(board.GP4)
led.direction = digitalio.Direction.OUTPUT
dht = adafruit_dht.DHT11(board.GP15)
#pwm = pwmio.PWMOut(board.GP16, frequency=2700, duty_cycle=2**15,
#       variable_frequency=True)
buzzer = digitalio.DigitalInOut(board.GP16)
buzzer.direction = digitalio.Direction.OUTPUT


i2c = busio.I2C(board.GP13, board.GP12)
lcd = GroveLCD(i2c, cols=16, rows=2)
lcd.message = "Hello\nCircuitPython!"
connect_wifi(creds.ssid, creds.psk)
pool = socketpool.SocketPool(wifi.radio)

# tz_offset is in hours; Paris is +2 in summer (CEST), +1 in winter (CET)
ntp = adafruit_ntp.NTP(pool, tz_offset=2, cache_seconds=3600)

rtc.RTC().datetime = ntp.datetime   # set the internal RTC once


count = 0
while True:
    state = step(state)
    now = time.monotonic()

    if state != last_state:               # menu actually changed
        print('buzzing...')
        buzzer.value = True
        #pwm.duty_cycle = 2**15            # start beep
        beep_until = now + BEEP_TIME

    if beep_until and now >= beep_until:  # stop beep
        print('stopped buzzing')
        buzzer.value = False
        #pwm.duty_cycle = 0
        beep_until = 0.0


    if state != last_state or now - last_draw >= 1.0:
        lcd.clear()
        MENUS[state]()
        last_state = state
        last_draw = now

