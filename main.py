import time
import Adafruit_GPIO.SPI as SPI
import RPi.GPIO as GPIO
import Adafruit_MCP3008
from adafruit_mcp3xxx.analog_in import AnalogIn
import requests
import serial
import pynmea2
import math


UBIDOTS_TOKEN = "BBFF-03MEmiXujs99bPymSwqiVXcNo5t545"
DEVICE_LABEL = "raspberry-pi" 
VARIABLE_LABEL_1 = "water-level-device"
VARIABLE_LABEL_2 = "encoder-device"
VARIABLE_LABEL_3 = "position-device"
VARIABLE_LABEL_4 = "speed-device"

CLK = 11
MISO = 9
MOSI = 10
CS = 8
mcp = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI)

def read_adc(channel):
    return mcp.read_adc(channel)

PULSES_PER_REVOLUTION = 20

def calculate_rpm(pulses, time_elapsed):
    return (pulses / PULSES_PER_REVOLUTION) / (time_elapsed / 60)

def convert_to_liters(raw_value):
    max_raw_value = 1023
    total_capacity = 30
    liters = (raw_value / max_raw_value) * total_capacity
    return liters   

SERIAL_PORT = "/dev/ttyS0"
BAUDRATE = 9600

prev_latitude = None
prev_longitude = None
prev_time = None

def read_gps_coordinates():
    ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)
    try:
        while True:
            raw_data = ser.readline().decode('utf-8')
            if raw_data.startswith('$GPGGA'):
                msg = pynmea2.parse(raw_data)
                latitude = msg.latitude
                longitude = msg.longitude
                return latitude, longitude
    except KeyboardInterrupt:
        ser.close()
        return None, None

def calculate_speed(curr_latitude, curr_longitude, curr_time):
    global prev_latitude, prev_longitude, prev_time

    if prev_latitude is None or prev_longitude is None or prev_time is None:
        prev_latitude = curr_latitude
        prev_longitude = curr_longitude
        prev_time = curr_time
        return 0.0

    time_diff = (curr_time - prev_time)
    distance = haversine(prev_latitude, prev_longitude, curr_latitude, curr_longitude)

    speed = distance / time_diff

    prev_latitude = curr_latitude
    prev_longitude = curr_longitude
    prev_time = curr_time

    return speed

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi_1 = math.radians(lat1)
    phi_2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi_1) * math.cos(phi_2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance

def build_payload(water_level_convert_to_liter, rpm, latitude, longitude, speed):
    payload = {
        VARIABLE_LABEL_1:water_level_convert_to_liter,
        VARIABLE_LABEL_2: rpm,
        VARIABLE_LABEL_3:{"lat": latitude,"lng": longitude},
        VARIABLE_LABEL_4: speed}
    return payload


def post_request(payload):
    url = "http://industrial.api.ubidots.com"
    url = "{}/api/v1.6/devices/{}".format(url, DEVICE_LABEL)
    headers = {"X-Auth-Token": UBIDOTS_TOKEN, "Content-Type": "application/json"}
    try:
        req = requests.post(url=url, headers=headers, json=payload)
        req.raise_for_status()
        print("[INFO] Data sent successfully")
    except requests.exceptions.RequestException as e:
        print("[ERROR] Failed to send data:", e)

try:
    while True:
        water_level_value = read_adc(0)
        water_level_convert_to_liter = convert_to_liters(water_level_value)

        ir_speed_value = read_adc(1)

        start_time = time.time()
        start_ir_speed = ir_speed_value
        time.sleep(1)
        end_ir_speed = read_adc(1)
        end_time = time.time()
        
        ir_speed_change = end_ir_speed - start_ir_speed
        rpm = calculate_rpm(ir_speed_change, end_time - start_time)
        
        latitude, longitude = read_gps_coordinates()
        if latitude is not None and longitude is not None:
            curr_time = time.time()
            speed = calculate_speed(latitude, longitude, curr_time)
        else:
            speed = None
        
        payload = build_payload(water_level_convert_to_liter, rpm, latitude, longitude, speed)
        post_request(payload)
        time.sleep(1)

except KeyboardInterrupt:
    print("Proses berhenti oleh pengguna.")
