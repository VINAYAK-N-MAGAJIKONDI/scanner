# -*- coding: utf-8 -*-
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore import Increment, FieldFilter
from datetime import datetime
from datetime import timezone
import time


cred = credentials.Certificate('key.json')
firebase_admin.initialize_app(cred)

# Get Firestore client
db = firestore.client()


import RPi.GPIO as GPIO
import time

# GPIO pins
TRIG = 4
ECHO = 17

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

def get_distance():
    # Send 10µs pulse
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    # Wait for echo start (timeout after 0.01s)
    start_time = time.time()
    timeout = start_time + 0.01
    while GPIO.input(ECHO) == 0 and time.time() < timeout:
        start_time = time.time()

    # Wait for echo end (timeout after 0.02s)
    stop_time = time.time()
    timeout = stop_time + 0.02
    while GPIO.input(ECHO) == 1 and time.time() < timeout:
        stop_time = time.time()

    # Compute distance
    duration = stop_time - start_time
    distance = (duration * 34300) / 2

    return round(distance, 2)

try:
    while True:
        dist = get_distance()
        print(f"Distance: {dist} cm")
        time.sleep(1)
except KeyboardInterrupt:
    print("\nMeasurement stopped by user")
    GPIO.cleanup()