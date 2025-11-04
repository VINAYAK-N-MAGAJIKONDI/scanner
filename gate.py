import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore import Increment, FieldFilter
from datetime import datetime
from datetime import timezone
import time

# Initialize Firebase Admin SDK
cred = credentials.Certificate('key.json')
firebase_admin.initialize_app(cred)

# Get Firestore client
db = firestore.client()

def generate_uid():
    """Generate a unique Firebase Auth UID-like string"""
    import uuid
    return str(uuid.uuid4())

def create_user_if_not_exists(userid):
    """Create a new user if they don't exist"""
    # Validate userid format (3 digits)
    if not (isinstance(userid, str) and userid.isdigit() and MIN_USERID <= int(userid) <= MAX_USERID):
        print(f"Error: Invalid user ID format. Must be 3 digits between {MIN_USERID} and {MAX_USERID}")
        return False
    
    # Query to find user by userid field
    users_ref = db.collection('users').where(filter=FieldFilter('userid', '==', userid))
    users = list(users_ref.get())
    
    if not users:
        # Create new user document with generated UID
        uid = generate_uid()
        current_time = datetime.now(timezone.utc)
        
        new_user_ref = db.collection('users').document(uid)
        new_user_ref.set({
            'userid': userid,
            'name': f'User {userid}',
            'email': f'user{userid}@example.com',
            'photoURL': '',
            'wallet': {
                'balance': 1000,  # Initial balance of Rs. 1000
                'createdAt': current_time
            },
            'createdAt': current_time
        })
        print(f"Created new user {userid} with initial balance of Rs. 1000")
        return True
    return True

# Constants
PARKING_RATE_PER_HOUR = 50  # Rs. 50 per hour
ADMIN_UID = "admin123"  # Admin's Firebase Auth UID
MIN_USERID = 100  # Minimum 3-digit user ID
MAX_USERID = 999  # Maximum 3-digit user ID

def calculate_parking_fee(entry_time, exit_time):
    """Calculate parking fee based on duration"""
    # Convert to UTC if not already timezone-aware
    if entry_time.tzinfo is None:
        entry_time = entry_time.replace(tzinfo=timezone.utc)
    if exit_time.tzinfo is None:
        exit_time = exit_time.replace(tzinfo=timezone.utc)
    
    duration = exit_time - entry_time
    hours = duration.total_seconds() / 3600
    return round(hours * PARKING_RATE_PER_HOUR)

def log_transaction(userid, amount, transaction_type):
    """Log financial transactions and admin logs"""
    current_time = datetime.now(timezone.utc)
    
    # Get and increment log ID
    log_ref = db.collection('admin_logs').document('config')
    config = log_ref.get().to_dict()
    new_log_id = (config.get('last_log_id', 0) + 1) if config else 1
    
    # Create admin log
    admin_log = {
        'timestamp': current_time,
        'action': 'exit' if transaction_type == 'parking_fee' else transaction_type,
        'userid': userid,
        'fee_charged': amount if transaction_type == 'parking_fee' else 0,
        'gate_id': 'GATE_001'  # Can be configured as needed
    }
    
    # Create transaction log
    transaction_log = {
        'userid': userid,
        'amount': amount,
        'type': transaction_type,
        'timestamp': current_time
    }
    
    # Update both logs in a batch
    batch = db.batch()
    batch.set(db.collection('admin_logs').document(str(new_log_id)), admin_log)
    batch.set(db.collection('transaction_logs').document(), transaction_log)
    batch.update(log_ref, {'last_log_id': new_log_id})
    batch.commit()

def update_admin_wallet(amount):
    """Update admin wallet balance"""
    admin_ref = db.collection('users').document(ADMIN_UID)
    
    # Get current balance or create admin if doesn't exist
    admin_doc = admin_ref.get()
    current_time = datetime.now(timezone.utc)
    
    if not admin_doc.exists:
        admin_ref.set({
            'userid': 'ADMIN',
            'name': 'Admin',
            'email': 'admin@smartspot.com',
            'photoURL': '',
            'wallet': {
                'balance': amount,
                'total_collected': amount,
                'createdAt': current_time
            },
            'createdAt': current_time
        })
    else:
        # Update both balance and total_collected
        admin_ref.update({
            'wallet.balance': Increment(amount),
            'wallet.total_collected': Increment(amount)
        })

def get_user_by_userid(userid):
    """Get user document by userid"""
    users_ref = db.collection('users').where(filter=FieldFilter('userid', '==', userid))
    users = list(users_ref.get())
    return users[0] if users else None

def get_user_balance(userid):
    """Get user's wallet balance"""
    user_doc = get_user_by_userid(userid)
    if not user_doc:
        return None
    return user_doc.to_dict().get('wallet', {}).get('balance', 0)

def update_user_wallet(userid, amount):
    """Update user's wallet balance"""
    user_doc = get_user_by_userid(userid)
    if user_doc:
        db.collection('users').document(user_doc.id).update({
            'wallet.balance': Increment(-amount)
        })

def record_entry(userid):
    """Record vehicle entry"""
    # Create user if they don't exist
    if not create_user_if_not_exists(userid):
        return False
    
    # Get user document
    user_doc = get_user_by_userid(userid)
    if not user_doc:
        print(f"Error: User {userid} not found!")
        return False
    
    # Check if user already has an active parking session
    parking_query = db.collection('parking_sessions').where(filter=FieldFilter('userid', '==', userid)).where(filter=FieldFilter('status', '==', 'active'))
    if len(list(parking_query.get())) > 0:
        print(f"Error: User {userid} already has an active parking session!")
        return False

    # Create new parking session
    entry_time = datetime.now(timezone.utc)
    parking_session = {
        'userid': userid,
        'entry_time': entry_time,
        'status': 'active'
    }
    db.collection('parking_sessions').add(parking_session)
    print(f"Entry recorded for user {userid} at {entry_time}")
    return True

def record_exit(userid):
    """Record vehicle exit and process payment"""
    # Find active parking session
    parking_ref = db.collection('parking_sessions').where(filter=FieldFilter('userid', '==', userid)).where(filter=FieldFilter('status', '==', 'active'))
    sessions = list(parking_ref.get())
    
    if not sessions:
        print(f"Error: No active parking session found for user {userid}!")
        return False
    
    session = sessions[0]
    session_data = session.to_dict()
    exit_time = datetime.now(timezone.utc)
    
    # Calculate parking fee
    fee = calculate_parking_fee(session_data['entry_time'], exit_time)
    
    # Check user's wallet balance
    balance = get_user_balance(userid)
    if balance is None:
        print(f"Error: Wallet not found for user {userid}!")
        return False
    if balance < fee:
        print(f"Error: Insufficient balance! Required: {fee}, Available: {balance}")
        return False
    
    try:
        # Update user's wallet
        update_user_wallet(userid, fee)
        
        # Update admin's wallet
        update_admin_wallet(fee)
        
        # Log transaction
        log_transaction(userid, fee, 'parking_fee')
        
        # Update parking session
        db.collection('parking_sessions').document(session.id).update({
            'exit_time': exit_time,
            'fee_charged': fee,
            'status': 'completed'
        })
        
        print(f"Exit recorded for user {userid}")
        print(f"Parking fee: Rs. {fee}")
        print(f"Remaining balance: Rs. {balance - fee}")
        return True
        
    except Exception as e:
        print(f"Error processing payment: {str(e)}")
        return False

def main():
    """Main function to run the gate system"""
    print("=== Parking Gate System ===")
    print("Press Ctrl+C to exit the program")
    
    # Create admin user if it doesn't exist
    admin_ref = db.collection('users').document(ADMIN_UID)
    if not admin_ref.get().exists:
        current_time = datetime.now(timezone.utc)
        admin_ref.set({
            'userid': 'ADMIN',
            'name': 'Admin',
            'email': 'admin@smartspot.com',
            'photoURL': '',
            'wallet': {
                'balance': 0,
                'total_collected': 0,
                'createdAt': current_time
            },
            'createdAt': current_time
        })
        print("Created admin user")
    
    # Initialize admin logs collection if needed
    log_ref = db.collection('admin_logs').document('config')
    if not log_ref.get().exists:
        log_ref.set({'last_log_id': 0})
    
    while True:
        try:
            userid = input("\nScan user ID (or press Enter): ").strip()
            if not userid:
                continue
                
            # Check if user has active session
            parking_ref = db.collection('parking_sessions').where(filter=FieldFilter('userid', '==', userid)).where(filter=FieldFilter('status', '==', 'active'))
            active_sessions = list(parking_ref.get())
            
            if active_sessions:
                # For exit: user must have exactly one active session
                if len(active_sessions) == 1:
                    # Get the last entry timestamp
                    last_entry = active_sessions[0].get('entry_time')
                    if last_entry:
                        current_time = datetime.now(timezone.utc)
                        time_diff = current_time - last_entry
                        
                        # If last entry was less than 30 seconds ago, ignore the scan
                        if time_diff.total_seconds() < 30:
                            print("Please wait before scanning again...")
                            continue
                            
                    if record_exit(userid):
                        time.sleep(1)  # Delay after successful exit
                else:
                    print(f"Error: Multiple active sessions found for user {userid}. Please contact admin.")
            else:
                # For entry: proceed with entry record
                if record_entry(userid):
                    time.sleep(1)  # Delay after successful entry
                    
            time.sleep(0.2)  # Small delay to prevent rapid repeated scans
            
        except KeyboardInterrupt:
            print("\nShutting down gate system...")
            break
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()