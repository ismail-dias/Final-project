import requests
import RPi.GPIO as GPIO
import time

UBIDOTS_TOKEN = "BBFF-03MEmiXujs99bPymSwqiVXcNo5t545"
DEVICE_LABEL = "raspberry-pi-motor"
VARIABLE_LABEL_1 = "motor-command"

# Konfigurasi GPIO
GPIO.setmode(GPIO.BCM)
pin_relay = 18
GPIO.setup(pin_relay, GPIO.OUT)
GPIO.setwarnings(False)

# def build_payload(relay):
#     payload = {
#         VARIABLE_LABEL_1:relay}
#     return payload

try:
    while True:
        url = "http://industrial.api.ubidots.com"
        url = "{}/api/v1.6/devices/{}/{}/lv".format(url, DEVICE_LABEL, VARIABLE_LABEL_1)
        params = {"page_size":1}
        headers = {"X-Auth-Token": UBIDOTS_TOKEN}
        #try:
        req = requests.get(url, headers=headers, params=params)
        print(req)
        last_values = req.json()
        if last_values == 1:
            GPIO.output(pin_relay, GPIO.LOW)
        else:
            GPIO.output(pin_relay, GPIO.HIGH)
except KeyboardInterrupt:
    GPIO.cleanup()

