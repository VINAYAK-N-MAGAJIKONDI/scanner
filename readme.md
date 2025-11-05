# Smart Parking Gate System with QR Scanning

A Python-based parking management system integrated with **Firebase Firestore** that handles user accounts, parking sessions, automated billing, and QR code scanning for vehicle entry/exit. Users have digital wallets, and admin balances are updated automatically.

---

## Features

* **User Management**

  * Automatic user creation on first scan.
  * Users are assigned a unique ID, email, and initial wallet balance of Rs. 1000.
  * Validation for user IDs (3-digit numeric IDs between 100–999).

* **Parking Session Management**

  * Track vehicle entry and exit with timestamps.
  * Prevent multiple active sessions per user.
  * Calculate parking fees (Rs. 50/hour, minimum Rs. 50).

* **Wallet & Transactions**

  * Deduct parking fees from user wallets.
  * Update admin wallet balance automatically.
  * Log transactions in Firestore (`transaction_logs` and `admin_logs` collections).

* **Admin Management**

  * Auto-create admin account if not present.
  * Tracks total collected fees.
  * Maintains incremental log IDs for admin actions.

* **QR Code Support**

  * Detect QR codes using OpenCV’s `QRCodeDetector`.
  * Optionally fallback to terminal input if camera/QR scanning is unavailable.
  * Visual feedback: Draws polygon around QR code in camera frame.

* **Security & Validation**

  * Prevents rapid re-scanning (less than 30 seconds) to avoid double charges.
  * Ensures correct session handling for entry/exit.

---

## Tech Stack

* **Language:** Python 3.x
* **Database:** Firebase Firestore
* **Libraries & Tools:**

  * `firebase_admin` – Firebase Admin SDK
  * `google.cloud.firestore` – Firestore operations
  * `datetime` – Handling timestamps
  * `uuid` – Unique ID generation
  * `cv2` (OpenCV) – QR code scanning (optional)
  * `numpy` – Image processing support for OpenCV

---

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd smart-parking-gate
```

2. Install dependencies:

```bash
pip install firebase-admin google-cloud-firestore opencv-python numpy
```

3. Add your Firebase Admin SDK key:

* Save your service account JSON file as `key.json` in the project root.

---

## Configuration

* Update the constants in the script:

```python
PARKING_RATE_PER_HOUR = 50   # Parking fee per hour
ADMIN_UID = "admin123"       # Admin's UID
MIN_USERID = 100              # Minimum valid user ID
MAX_USERID = 999              # Maximum valid user ID
```

* QR scanning uses the default camera index 0. Adjust in `scan_qr_from_camera(camera_index=0)` if needed.

---

## Usage

1. Run the main script:

```bash
python parking_gate_system.py
```

2. **QR Mode:** If OpenCV is installed and a camera is available:

* The system opens a camera window and detects QR codes.
* On successful scan, it records entry/exit and processes payments automatically.

3. **Fallback Mode:** If camera or OpenCV is unavailable:

* The system prompts for user ID input via terminal:

```
Scan user ID (or press Enter):
```

4. **Exit the program:** Press **Ctrl+C**.

---

## Firestore Collections

| Collection Name    | Description                                                                      |
| ------------------ | -------------------------------------------------------------------------------- |
| `users`            | Stores user information, wallet balance, and metadata.                           |
| `parking_sessions` | Tracks active and completed parking sessions with timestamps.                    |
| `transaction_logs` | Records user wallet transactions and fees.                                       |
| `admin_logs`       | Logs admin activities and parking fee collection, including incremental log IDs. |

---

## Functions Overview

* **User & Wallet Management**

  * `create_user_if_not_exists(userid)` – Create a new user if not present.
  * `get_user_by_userid(userid)` – Fetch user document.
  * `get_user_balance(userid)` – Retrieve wallet balance.
  * `update_user_wallet(userid, amount)` – Deduct amount from user wallet.
  * `update_admin_wallet(amount)` – Update admin wallet and total collected.

* **Parking Management**

  * `record_entry(userid)` – Logs vehicle entry.
  * `record_exit(userid)` – Logs vehicle exit and handles payment.
  * `calculate_parking_fee(entry_time, exit_time)` – Compute parking charges.

* **Transactions & Logs**

  * `log_transaction(userid, amount, transaction_type)` – Record transactions and admin logs.

* **QR Scanning**

  * `scan_qr_from_camera(camera_index=0, timeout=10)` – Detect QR code via OpenCV camera.

---

## Notes

* All timestamps are stored in UTC.
* Minimum parking fee is Rs. 50.
* Users can have only one active session at a time.
* Admin is automatically created with UID `admin123` if missing.
* QR code scanning is optional; terminal input is a fallback.

---

## Future Improvements

* Integrate IoT sensors for automatic parking slot detection.
* Add a web dashboard to monitor sessions, transactions, and wallet balances.
* Enable multi-gate support with configurable gate IDs.
* Notify users for low wallet balance.
* Implement automated QR code generation per user for faster scanning.

---

## License

MIT License – Open-source and free to use.

---

