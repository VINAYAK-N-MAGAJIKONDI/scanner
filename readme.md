# Smart Parking Gate System

A Python-based parking management system using **Firebase Firestore** to handle user accounts, vehicle entry/exit, and automated billing. This system supports real-time wallet management for users, tracks parking sessions, logs transactions, and updates admin balances automatically.

---

## Features

* **User Management**

  * Create users automatically when they first enter the parking lot.
  * Users are assigned a unique ID, email, and an initial wallet balance (Rs. 1000).

* **Parking Session Management**

  * Record vehicle entry and exit with timestamps.
  * Detect and prevent duplicate active sessions.
  * Calculate parking fees based on duration (Rs. 50 per hour).

* **Wallet & Transactions**

  * Deduct parking fees from the user’s wallet.
  * Update admin wallet balance automatically.
  * Log transactions in Firestore (`transaction_logs` and `admin_logs` collections).

* **Admin Management**

  * Admin account is created automatically if not present.
  * Tracks total collected parking fees.
  * Maintains an incremental log of parking activities.

* **Security & Validation**

  * User ID validation (3-digit numeric IDs between 100–999).
  * Prevents rapid re-scanning (less than 30 seconds) to avoid double charges.

---

## Tech Stack

* **Language:** Python 3.x
* **Database:** Firebase Firestore
* **Libraries & Tools:**

  * `firebase_admin` – Firebase Admin SDK
  * `google.cloud.firestore` – Firestore operations
  * `datetime` – Handling time and timestamps
  * `uuid` – Unique ID generation

---

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd smart-parking-gate
```

2. Install dependencies:

```bash
pip install firebase-admin google-cloud-firestore
```

3. Add your Firebase Admin SDK key:

* Save your service account JSON file as `key.json` in the project root.

---

## Configuration

* Update the following constants in the script:

```python
PARKING_RATE_PER_HOUR = 50   # Parking fee per hour
ADMIN_UID = "admin123"       # Admin's UID
MIN_USERID = 100              # Minimum valid user ID
MAX_USERID = 999              # Maximum valid user ID
```

---

## Usage

1. Run the main script:

```bash
python parking_gate_system.py
```

2. The system will prompt:

```
Scan user ID (or press Enter):
```

* **Entry:** Scan a new or existing user ID. The system creates the user if not found and records the entry time.
* **Exit:** Scan a user ID with an active session. The system calculates the parking fee, deducts from the wallet, updates admin balance, and logs the transaction.

3. Press **Ctrl+C** to stop the system.

---

## Firestore Collections

| Collection Name    | Description                                                                      |
| ------------------ | -------------------------------------------------------------------------------- |
| `users`            | Stores user info, wallet balance, and metadata.                                  |
| `parking_sessions` | Tracks active and completed parking sessions with entry/exit times.              |
| `transaction_logs` | Records user wallet transactions and fees.                                       |
| `admin_logs`       | Logs admin activities and parking fee collection, including incremental log IDs. |

---

## Functions Overview

* **`create_user_if_not_exists(userid)`** – Creates a new user if they don’t exist.
* **`record_entry(userid)`** – Logs vehicle entry for a user.
* **`record_exit(userid)`** – Logs vehicle exit and handles payment processing.
* **`calculate_parking_fee(entry_time, exit_time)`** – Calculates parking charges.
* **`update_user_wallet(userid, amount)`** – Deducts parking fee from user wallet.
* **`update_admin_wallet(amount)`** – Updates admin wallet balance and total collected.
* **`log_transaction(userid, amount, transaction_type)`** – Records all transactions and admin logs.

---

## Notes

* All timestamps are stored in UTC.
* Users can have only one active session at a time.
* Parking fee is rounded to the nearest integer.
* Ensure Firebase Firestore has read/write permissions for the Admin SDK.

---

## Future Improvements

* Integrate with an IoT module to automatically detect free/occupied spots.
* Add QR code or NFC scanning for faster entry/exit.
* Implement a web dashboard to visualize sessions and transactions.
* Add notifications for low wallet balance.
* Support multi-gate setups with configurable gate IDs.

---

## License

This project is open-source and free to use under the MIT License.

---

## Author

Vinayak Magajikondi
