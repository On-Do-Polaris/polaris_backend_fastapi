# Local Database Setup Guide

## PostgreSQL Datawarehouse Configuration

This guide explains how to configure and test the PostgreSQL Datawarehouse connection for local development.

## Database Credentials

```
Host: localhost
Port: 5433
Database: skala_datawarehouse
User: skala_dw_user
Password: 1234
```

## Configuration Files

### 1. Environment Variables (.env)

The `.env` file contains the database connection string:

```bash
# Database URL (Datawarehouse - Local Development)
DATABASE_URL=postgresql://skala_dw_user:1234@localhost:5433/skala_datawarehouse
```

**Note:** The `.env` file is already configured with the correct credentials.

### 2. FastAPI Configuration (src/core/config.py)

The FastAPI application reads database configuration from environment variables:

```python
class Settings(BaseSettings):
    # Database (PostgreSQL Datawarehouse)
    # Default: Local development datawarehouse
    DATABASE_URL: Optional[str] = "postgresql://skala_dw_user:1234@localhost:5433/skala_datawarehouse"
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": "True",
        "extra": "ignore"
    }
```

**Priority:** Environment variables > .env file > default values

### 3. DatabaseManager (ai_agent/utils/database.py)

The `DatabaseManager` class handles all database operations:

```python
from ai_agent.utils.database import DatabaseManager

# Initialize with environment variable
db = DatabaseManager()  # Uses DATABASE_URL from environment

# Or initialize with explicit URL
db = DatabaseManager(database_url="postgresql://skala_dw_user:1234@localhost:5433/skala_datawarehouse")
```

## Starting the Database

### Option 1: Docker (Recommended)

```bash
# Start PostgreSQL container
docker-compose up -d postgres

# Check status
docker ps | grep postgres
```

### Option 2: Local PostgreSQL

```bash
# Start PostgreSQL service
sudo systemctl start postgresql

# Or on Windows with PostgreSQL installed
pg_ctl start -D "C:\Program Files\PostgreSQL\16\data"
```

## Testing the Connection

### Quick Test

```bash
# Set environment variable (Linux/Mac)
export DATABASE_URL="postgresql://skala_dw_user:1234@localhost:5433/skala_datawarehouse"

# Set environment variable (Windows PowerShell)
$env:DATABASE_URL="postgresql://skala_dw_user:1234@localhost:5433/skala_datawarehouse"

# Run test script
python test_fastapi_db_integration.py
```

### Comprehensive Integration Test

The project includes a comprehensive test script that verifies:

1. FastAPI configuration loading
2. DatabaseManager initialization
3. PostgreSQL connection
4. Database queries
5. Table existence and record counts

**Run the test:**

```bash
python test_fastapi_db_integration.py
```

**Expected output:**

```
======================================================================
FastAPI + Database Integration Test
======================================================================

[1] FastAPI Configuration:
    DATABASE_URL: postgresql://skala_dw_user:1234@localhost:5433/skala_datawarehouse
    [OK] FastAPI settings loaded successfully

[2] DatabaseManager Initialization:
    [OK] DatabaseManager initialized

[3] Database Connection Test:
    [OK] Connection successful!
    PostgreSQL version: PostgreSQL 16.4...

[4] Database Table Query:
    [OK] Found 10 tables

...

[OK] FastAPI Configuration: Working
[OK] DatabaseManager: Working
[OK] PostgreSQL Connection: Working
[OK] Database Queries: Working
```

## Database Schema

The datawarehouse includes the following tables:

### Climate Data Tables
- `location_grid` - Grid points for climate data
- `location_admin` - Administrative regions
- `ta_data` - Temperature data (monthly)
- `rn_data` - Rainfall data (monthly)
- `ws_data` - Wind speed data (monthly)
- `tamax_data` - Maximum temperature (daily)
- `tamin_data` - Minimum temperature (daily)
- `csdi_data`, `wsdi_data`, `rx1day_data`, `rx5day_data` - Climate indices (yearly)
- `sea_level_grid`, `sea_level_data` - Sea level rise data

### API Cache Tables
- `api_hospitals` - Hospital locations
- `api_shelters` - Emergency shelters
- `typhoon_besttrack` - Historical typhoon tracks
- `api_buildings`, `api_coastal_infrastructure`, `api_firestations`, etc.

### Spatial Analysis Cache
- `spatial_landcover` - Land cover analysis results
- `spatial_dem` - DEM analysis results (elevation, slope, aspect)

## Populating the Database

If tables are empty, run the ETL scripts to populate data:

```bash
cd ETL

# Install ETL dependencies
pip install -r requirements.txt

# Run data loading scripts
python scripts/load_monthly_grid_data.py
python scripts/load_yearly_grid_data.py
python scripts/load_sgg261_data.py
python scripts/load_sea_level_netcdf.py

# Check ETL documentation
cat README.md
```

## Using DatabaseManager in Code

### Basic Usage

```python
from ai_agent.utils.database import DatabaseManager

# Initialize
db = DatabaseManager()

# Execute SELECT query
results = db.execute_query(
    "SELECT * FROM location_grid LIMIT 10"
)

# Execute INSERT/UPDATE/DELETE
rows_affected = db.execute_update(
    "UPDATE location_grid SET latitude = %s WHERE grid_id = %s",
    (37.5665, 1)
)
```

### Location Queries

```python
# Find nearest climate grid point
grid = db.find_nearest_grid(latitude=37.5665, longitude=126.9780)
print(f"Nearest grid: {grid['grid_id']}, Distance: {grid['distance_meters']}m")

# Find administrative region
admin = db.find_admin_by_coords(latitude=37.5665, longitude=126.9780)
print(f"Admin region: {admin['admin_name']}")
```

### Climate Data Queries

```python
# Fetch monthly climate data
monthly_data = db.fetch_monthly_grid_data(
    grid_id=1234,
    start_date="2020-01-01",
    end_date="2020-12-31",
    scenario_id=2,  # SSP2-4.5
    variables=['ta', 'rn', 'ws']
)

# Fetch yearly climate indices
yearly_data = db.fetch_yearly_grid_data(
    grid_id=1234,
    start_year=2020,
    end_year=2050,
    scenario_id=2,
    variables=['csdi', 'wsdi', 'rx1day', 'rx5day']
)

# Fetch sea level rise data
sea_level = db.fetch_sea_level_data(
    latitude=35.1796,
    longitude=129.0756,
    start_year=2020,
    end_year=2100,
    scenario_id=2
)
```

### Comprehensive Data Collection

```python
# Collect all climate data for a location
all_data = db.collect_all_climate_data(
    latitude=37.5665,
    longitude=126.9780,
    start_year=2020,
    end_year=2050,
    scenario_id=2,  # SSP2-4.5
    admin_code="1101010100"  # Optional
)

print("Grid:", all_data['grid'])
print("Admin:", all_data['admin'])
print("Monthly data:", all_data['monthly_data'])
print("Yearly data:", all_data['yearly_data'])
print("Daily data:", all_data['daily_data'])
print("Sea level data:", all_data['sea_level_data'])
```

## Troubleshooting

### Issue: "Connection refused" or "could not connect to server"

**Solution:** Make sure PostgreSQL is running on port 5433

```bash
# Check if PostgreSQL is running
docker ps | grep postgres
# or
sudo systemctl status postgresql
```

### Issue: "FATAL: password authentication failed"

**Solution:** Verify credentials in `.env` file match database user

```bash
# Check .env file
cat .env | grep DATABASE_URL

# Should be:
# DATABASE_URL=postgresql://skala_dw_user:1234@localhost:5433/skala_datawarehouse
```

### Issue: "relation does not exist" or empty tables

**Solution:** Run ETL scripts to populate the database

```bash
cd ETL
python scripts/load_monthly_grid_data.py
```

### Issue: Settings not loading from .env file

**Solution:** Ensure environment variable is set (overrides .env file)

```bash
# Linux/Mac
export DATABASE_URL="postgresql://skala_dw_user:1234@localhost:5433/skala_datawarehouse"

# Windows PowerShell
$env:DATABASE_URL="postgresql://skala_dw_user:1234@localhost:5433/skala_datawarehouse"
```

**Or** restart your terminal to clear any cached environment variables.

## Integration with FastAPI

When running the FastAPI server, it will automatically use the configured database:

```bash
# Set environment variable
export DATABASE_URL="postgresql://skala_dw_user:1234@localhost:5433/skala_datawarehouse"

# Start server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The AI agents will use `DatabaseManager` to fetch climate data during analysis:

```python
# In data_collection_agent.py
from ai_agent.utils.database import DatabaseManager

db = DatabaseManager()
climate_data = db.collect_all_climate_data(
    latitude=site_latitude,
    longitude=site_longitude,
    start_year=2020,
    end_year=2050
)
```

## Summary

1. **Database credentials** are configured in `.env` file
2. **FastAPI config** (`src/core/config.py`) loads from environment variables
3. **DatabaseManager** (`ai_agent/utils/database.py`) handles all database operations
4. **Test scripts** verify the integration is working correctly
5. **ETL scripts** populate the database with climate data

**All systems operational!** The local database is properly configured and ready for development.
