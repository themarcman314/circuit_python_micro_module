import board
import busio
import digitalio
import time
import adafruit_datetime as datetime
import adafruit_dht
from grove_lcd import GroveLCD


def disp_time(lcd:GroveLCD):
    time = datetime.datetime.now()
    lcd.write_line(0, time.strftime("%H:%M:%S"))


def disp_weather(lcd:GroveLCD, dht:adafruit_dht.DHT11):
    try:
        temp = dht.temperature
        humity = dht.humidity
        lcd.write_line(0, f"Temp: {temp} C")
        lcd.write_line(1, f"Humidity: {humity} %")
    except RuntimeError as e:
        # DHT sensors often fail a read; just retry next loop
        print("DHT read error:", e)


led = digitalio.DigitalInOut(board.GP4)
led.direction = digitalio.Direction.OUTPUT
dht = adafruit_dht.DHT11(board.GP15)

i2c = busio.I2C(board.GP13, board.GP12)
lcd = GroveLCD(i2c, cols=16, rows=2)
lcd.message = "Hello\nCircuitPython!"

count = 0
while True:
    count += 1
    time.sleep(5)
    led.value = not led.value
    disp_weather(lcd, dht)
    #disp_time(lcd)

