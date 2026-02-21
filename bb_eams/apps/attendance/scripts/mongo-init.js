db = db.getSiblingDB('bbeams_db');

// Create collections with validation
db.createCollection('users');
db.createCollection('departments');
db.createCollection('devices');
db.createCollection('policies');
db.createCollection('attendance_records');
db.createCollection('leave_requests');

// Create indexes
db.users.createIndex({ "username": 1 }, { unique: true });
db.users.createIndex({ "email": 1 }, { unique: true });
db.users.createIndex({ "employee_id": 1 }, { unique: true, sparse: true });
db.users.createIndex({ "department_id": 1 });

db.attendance_records.createIndex({ "user_id": 1, "timestamp": -1 });
db.attendance_records.createIndex({ "device_id": 1, "timestamp": -1 });

db.leave_requests.createIndex({ "user_id": 1, "status": 1 });
db.leave_requests.createIndex({ "start_date": 1, "end_date": 1 });