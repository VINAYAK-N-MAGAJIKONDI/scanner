# Firebase Database Structure - Smart Spot

## Overview
This document outlines the complete Firestore database structure for the Smart Spot parking management system, including both the mobile app and gate management system.

## Collections Structure

### 1. `users` Collection
User profiles and wallet information.
```
users/
├─ {uid}/              # Firebase Auth UID
   ├─ userid: string   # 3-digit unique identifier
   ├─ name: string    
   ├─ email: string
   ├─ photoURL: string
   ├─ wallet: {
   │   └─ balance: number  # Current wallet balance
   │   └─ createdAt: timestamp
   }
   └─ createdAt: timestamp

# Special Admin User
users/
└─ admin123/          # Admin account
   ├─ wallet: {
   │   ├─ balance: number       # Admin wallet balance
   │   └─ total_collected: number  # Total parking fees collected
   }
   └─ createdAt: timestamp
```

### 2. `parkslot` Collection
Parking spot information.
```
parkslot/
├─ {spot_id}/
   ├─ name: string     # Name/identifier of the spot
   ├─ lat: number      # Latitude
   ├─ long: number     # Longitude
   └─ available: number  # Number of available spaces
```

### 3. `parking_sessions` Collection
Active and completed parking sessions.
```
parking_sessions/
├─ {session_id}/
   ├─ user_id: string           # User's 3-digit ID
   ├─ entry_time: timestamp     # Entry timestamp (UTC)
   ├─ exit_time: timestamp      # Exit timestamp (UTC)
   ├─ status: string           # "active" | "completed"
   ├─ fee_charged: number      # Amount charged for the session
   └─ gate_id: string         # Identifier of the gate used
```

### 4. `admin_logs` Collection
System logs for auditing and monitoring.
```
admin_logs/
├─ {log_id}/
   ├─ timestamp: timestamp    # When the action occurred
   ├─ action: string         # "entry" | "exit"
   ├─ user_id: string        # User's 3-digit ID
   ├─ fee_charged: number    # Amount charged (for exits)
   ├─ gate_id: string        # Gate identifier
   └─ session_id: string     # Reference to parking session
```

## Important Rules & Constraints

1. User IDs
   - Each user has a Firebase Auth UID (for authentication)
   - Each user also has a 3-digit `userid` (for QR codes)
   - `userid` must be unique across all users

2. Wallet System
   - User wallets cannot have negative balance
   - All transactions are atomic using Firestore transactions
   - Admin wallet tracks total_collected separately from balance

3. Parking Sessions
   - A user can only have one active session at a time
   - Sessions must be completed (exit) before starting new ones
   - All timestamps are stored in UTC

## Rate Configuration

Current parking rates are configured in the gate system:
- Base Rate: ₹50 per hour
- Minimum Charge: ₹20 (applicable for stays under 1 hour)
- Rates are rounded up to the nearest hour

## Security Considerations

1. User Document Access
   - Users should only read/write their own user document
   - Only the gate system should modify wallet balances
   - Admin can read all user documents

2. Parking Sessions
   - Users can read their own sessions
   - Only gate system can create/modify sessions
   - Admin can read all sessions

3. Admin Logs
   - Read/write restricted to admin and gate system
   - Users cannot access admin logs

## Example Security Rules

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // User profiles
    match /users/{userId} {
      allow read: if request.auth.uid == userId;
      allow write: if request.auth.uid == userId 
        && !request.resource.data.wallet; // Can't modify wallet directly
    }
    
    // Parking spots
    match /parkslot/{spotId} {
      allow read: if request.auth != null;
      allow write: if false; // Only backend can modify
    }
    
    // Sessions and logs
    match /parking_sessions/{sessionId} {
      allow read: if request.auth != null 
        && resource.data.user_id == request.auth.uid;
    }
    
    match /admin_logs/{logId} {
      allow read, write: if false; // Only backend access
    }
  }
}
```

## Integration Points

1. Mobile App (React)
   - Reads user profile and wallet
   - Displays QR code using 3-digit userid
   - Shows available parking spots
   - Manages wallet top-ups

2. Gate System (Python)
   - Scans QR codes
   - Creates/completes parking sessions
   - Manages payment processing
   - Generates admin logs

## Backup Considerations

Critical collections to backup:
1. `users` - Contains wallet balances
2. `parking_sessions` - Legal record of parking usage
3. `admin_logs` - Audit trail of all operations

## Development Setup

1. Enable Firebase services:
   - Authentication (Google sign-in)
   - Firestore Database
   - Generate Admin SDK key for gate system

2. Configure security rules:
   - Deploy provided security rules
   - Test rules with Security Rules Simulator

3. Initial Setup:
   - Create admin user document
   - Configure initial parking spots
   - Set up monitoring on admin_logs