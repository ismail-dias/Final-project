from ubidots import ApiClient
import RPi.GPIO as GPIO
import time


# Konfigurasi Ubidots
UBIDOTS_TOKEN = "BBFF-03MEmiXujs99bPymSwqiVXcNo5t545"
DEVICE_LABEL = "raspberry-pi-motor"

api = ApiClient(token="BBFF-03MEmiXujs99bPymSwqiVXcNo5t545")
variable = api.get_variable("64e36cbbf9da915170e8fb71")

# Konfigurasi GPIO
GPIO.setmode(GPIO.BCM)
pin_relay = 18
GPIO.setup(pin_relay, GPIO.OUT)
GPIO.setwarnings(False)

try:
    while True:
        last_value = variable.get_values(1)
        if last_value[0].get("value") == 1:
            GPIO.output(pin_relay, GPIO.LOW)
            time.sleep(0.1)
        else:
            GPIO.output(pin_relay, GPIO.HIGH)
            time.sleep(0.1)
            
except KeyboardInterrupt:
    GPIO.cleanup()
