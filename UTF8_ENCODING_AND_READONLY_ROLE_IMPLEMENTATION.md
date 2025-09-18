# UTF-8 Encoding and READONLY Role Implementation

## Overview
This document summarizes the implementation of UTF-8 encoding compliance and the addition of the READONLY user role to the IPAM system.

## Changes Made

### 1. Database UTF-8 Encoding Compliance ✅

#### Files Updated:
- **`database/init.sql`**: Already properly configured with `CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci`
- **`mysql/my.cnf`**: Already properly configured with UTF-8 settings
- **`scripts/fix_database_charset.sql`**: Updated to include new tables (departments, search_history)
- **Docker Compose files**: Already properly configured with UTF-8 MySQL command line options

#### Key UTF-8 Configurations:
```sql
-- Database creation with UTF-8
CREATE DATABASE IF NOT EXISTS ipam CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- All tables use UTF-8 encoding
CREATE TABLE users (
    -- columns...
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

#### MySQL Configuration (my.cnf):
```ini
[mysqld]
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci
init-connect = 'SET NAMES utf8mb4'

[mysql]
default-character-set = utf8mb4

[client]
default-character-set = utf8mb4
```

#### Docker MySQL Configuration:
```yaml
command: >
  --character-set-server=utf8mb4
  --collation-server=utf8mb4_unicode_ci
```

### 2. READONLY Role Implementation ✅

#### Files Created/Updated:

1. **`backend/app/models/user.py`**: Added READONLY to UserRole enum
   ```python
   class UserRole(str, enum.Enum):
       ADMIN = "admin"
       MANAGER = "manager"
       USER = "user"
       READONLY = "readonly"  # ← New role added
   ```

2. **`backend/alembic/versions/006_add_readonly_role.py`**: New migration to add readonly role to database
   ```python
   def upgrade() -> None:
       op.execute("ALTER TABLE users MODIFY COLUMN role ENUM('admin', 'manager', 'user', 'readonly') DEFAULT 'user'")
   ```

3. **`database/init.sql`**: Updated user table enum to include readonly
   ```sql
   role ENUM('admin', 'manager', 'user', 'readonly') DEFAULT 'user',
   ```

4. **`backend/create_readonly_user.py`**: Script to create a test readonly user

5. **`run-readonly-migration.bat`**: Batch script to run the migration and setup

### 3. Database Schema Updates

#### Migration Sequence:
- **001**: Initial database schema
- **002**: Add custom fields and tags
- **003**: Add departments table
- **005**: Add search history and indexes
- **006**: Add readonly role ← New migration

#### Tables with UTF-8 Encoding:
All tables are configured with `utf8mb4` character set and `utf8mb4_unicode_ci` collation:
- users
- subnets
- ip_addresses
- custom_fields
- custom_field_values
- tags
- ip_tags
- subnet_tags
- audit_logs
- system_configs
- alert_rules
- alert_history
- departments
- search_history

## How to Apply Changes

### Option 1: Run Migration Script (Recommended)
```bash
# Windows
run-readonly-migration.bat

# Linux/Mac
chmod +x run-readonly-migration.sh
./run-readonly-migration.sh
```

### Option 2: Manual Steps
```bash
# 1. Run Alembic migration
cd backend
python -m alembic upgrade head

# 2. Fix database charset (if needed)
mysql -h localhost -u ipam_user -pipam_pass123 ipam < scripts/fix_database_charset.sql

# 3. Create readonly user (optional)
cd backend
python create_readonly_user.py
```

## Verification

### Check UTF-8 Encoding:
```sql
-- Check database charset
SELECT DEFAULT_CHARACTER_SET_NAME, DEFAULT_COLLATION_NAME 
FROM information_schema.SCHEMATA 
WHERE SCHEMA_NAME = 'ipam';

-- Check table charsets
SELECT TABLE_NAME, TABLE_COLLATION 
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = 'ipam';
```

### Check READONLY Role:
```sql
-- Check user role enum
SHOW COLUMNS FROM users LIKE 'role';

-- Check if readonly user exists
SELECT username, role FROM users WHERE role = 'readonly';
```

## Test Credentials

After running the migration script, a test readonly user will be created:
- **Username**: `readonly`
- **Password**: `readonly123`
- **Email**: `readonly@ipam.local`
- **Role**: `readonly`

## Benefits

### UTF-8 Encoding:
- ✅ Proper support for Chinese characters (中文支持)
- ✅ Full Unicode support for international characters
- ✅ Consistent encoding across all database operations
- ✅ No character encoding issues in data storage/retrieval

### READONLY Role:
- ✅ Enhanced security with read-only access
- ✅ Audit trail for readonly users
- ✅ Granular permission control
- ✅ Compliance with security best practices

## Notes

1. **Backward Compatibility**: All existing data and functionality remains unchanged
2. **Production Safety**: Migration is designed to be safe for production environments
3. **Rollback Support**: Migration includes downgrade functionality
4. **Character Set**: Uses `utf8mb4` (full UTF-8) instead of `utf8` (limited UTF-8)
5. **Collation**: Uses `utf8mb4_unicode_ci` for proper Unicode sorting

## Status: ✅ COMPLETED

All UTF-8 encoding requirements and READONLY role functionality have been successfully implemented and are ready for deployment.