import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timezone
import RPi.GPIO as GPIO
import time
import threading

# Initialize Firebase Admin SDK
cred = credentials.Certificate('key.json')
firebase_admin.initialize_app(cred)

# Get Firestore client
db = firestore.client()

# Constants
DISTANCE_THRESHOLD = 30  # Distance in cm to detect car
UPDATE_INTERVAL = 1  # Seconds between sensor readings

# GPIO Setup for 5 Ultrasonic Sensors
SENSORS = {
    'slotid1': {'TRIG': 17, 'ECHO': 27},
    'slotid2': {'TRIG': 22, 'ECHO': 23},
    'slotid3': {'TRIG': 24, 'ECHO': 25},
    'slotid4': {'TRIG': 5, 'ECHO': 6},
    'slotid5': {'TRIG': 19, 'ECHO': 26}
}

def setup_gpio():
    """Initialize GPIO pins for ultrasonic sensors"""
    GPIO.setmode(GPIO.BCM)
    for sensor in SENSORS.values():
        GPIO.setup(sensor['TRIG'], GPIO.OUT)
        GPIO.setup(sensor['ECHO'], GPIO.IN)
        GPIO.output(sensor['TRIG'], False)
    print("Sensor initialization completed")

def measure_distance(trig_pin, echo_pin):
    """Measure distance using ultrasonic sensor"""
    try:
        # Trigger ultrasonic measurement
        GPIO.output(trig_pin, True)
        time.sleep(0.00001)
        GPIO.output(trig_pin, False)

        # Wait for echo start
        pulse_start = time.time()
        timeout = pulse_start + 0.1  # 100ms timeout
        while GPIO.input(echo_pin) == 0:
            if time.time() > timeout:
                return None
            pulse_start = time.time()

        # Wait for echo end
        pulse_end = time.time()
        timeout = pulse_end + 0.1  # 100ms timeout
        while GPIO.input(echo_pin) == 1:
            if time.time() > timeout:
                return None
            pulse_end = time.time()

        # Calculate distance
        pulse_duration = pulse_end - pulse_start
        distance = pulse_duration * 17150  # Speed of sound * time / 2
        distance = round(distance, 2)

        return distance if 2 < distance < 400 else None  # Valid range check
    
    except Exception as e:
        print(f"Error measuring distance: {str(e)}")
        return None

def update_slot_status(slot_id, is_available, current_status):
    """Update slot status in Firebase"""
    try:
        # Get reference to slots document
        slots_ref = db.collection('parkslot').document('slots')
        
        # If status changed, update Firebase
        if current_status.get(slot_id) != is_available:
            # Update slot status and available count
            transaction = db.transaction()
            
            @firestore.transactional
            def update_in_transaction(transaction, slots_ref):
                slots = slots_ref.get(transaction=transaction).to_dict()
                
                # Calculate availability change
                old_status = slots.get(slot_id, True)
                if old_status != is_available:
                    # Update available count
                    current_available = slots.get('available', 0)
                    if is_available:
                        current_available += 1  # Slot became available
                    else:
                        current_available -= 1  # Slot became occupied
                    
                    # Update document
                    transaction.update(slots_ref, {
                        slot_id: is_available,
                        'available': current_available
                    })
                    
                    print(f"Updated {slot_id}: {'Available' if is_available else 'Occupied'}")
                    print(f"Total available slots: {current_available}")
            
            # Execute transaction
            update_in_transaction(transaction, slots_ref)
            
            # Update local status cache
            current_status[slot_id] = is_available
            
    except Exception as e:
        print(f"Error updating slot status: {str(e)}")

def monitor_sensors():
    """Continuously monitor all sensors and update Firebase"""
    current_status = {}  # Cache of current slot statuses
    
    try:
        while True:
            for slot_id, pins in SENSORS.items():
                # Measure distance
                distance = measure_distance(pins['TRIG'], pins['ECHO'])
                
                if distance is not None:
                    # Determine if slot is available (no car detected)
                    is_available = distance > DISTANCE_THRESHOLD
                    
                    # Update Firebase if status changed
                    update_slot_status(slot_id, is_available, current_status)
                
                time.sleep(0.1)  # Small delay between sensors
            
            time.sleep(UPDATE_INTERVAL)
            
    except KeyboardInterrupt:
        print("\nStopping sensor monitoring...")
        GPIO.cleanup()
    except Exception as e:
        print(f"Error in monitor_sensors: {str(e)}")
        GPIO.cleanup()

def initialize_slots():
    """Initialize slots document if it doesn't exist"""
    try:
        slots_ref = db.collection('parkslot').document('slots')
        if not slots_ref.get().exists:
            slots_ref.set({
                'slotid1': True,
                'slotid2': True,
                'slotid3': True,
                'slotid4': True,
                'slotid5': True,
                'available': 5
            })
            print("Initialized slots document")
    except Exception as e:
        print(f"Error initializing slots: {str(e)}")

def main():
    """Main function to run the parking sensor system"""
    print("=== Parking Sensor System ===")
    print("Press Ctrl+C to exit")
    
    # Initialize slots in Firebase
    initialize_slots()
    
    try:
        # Setup GPIO
        setup_gpio()
        time.sleep(2)  # Wait for sensors to stabilize
        
        # Start monitoring
        monitor_sensors()
        
    except KeyboardInterrupt:
        print("\nShutting down sensor system...")
    except Exception as e:
        print(f"Error in main: {str(e)}")
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main()