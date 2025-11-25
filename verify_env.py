#!/usr/bin/env python
"""Verify environment configuration"""
import os
import sys

print("=" * 60)
print("Environment Variable Check")
print("=" * 60)

# Check if DATABASE_URL is in environment
db_url_env = os.environ.get('DATABASE_URL')
print(f"\n1. DATABASE_URL in os.environ:")
if db_url_env:
    print(f"   Value: {db_url_env}")
    print(f"   [WARNING] Environment variable is set!")
else:
    print(f"   [OK] Not set (will use .env file)")

# Check .env file
print(f"\n2. DATABASE_URL in .env file:")
try:
    with open('.env', 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip().startswith('DATABASE_URL='):
                print(f"   {line.strip()}")
                break
except Exception as e:
    print(f"   [ERROR] Could not read .env: {e}")

# Load config
print(f"\n3. Loading src/core/config.py:")
try:
    from src.core.config import settings
    print(f"   DATABASE_URL: {settings.DATABASE_URL}")

    expected = "postgresql://skala_dw_user:1234@localhost:5433/skala_datawarehouse"
    if settings.DATABASE_URL == expected:
        print(f"   [OK] Correct value loaded!")
    else:
        print(f"   [WARNING] Unexpected value!")
        print(f"   Expected: {expected}")
except Exception as e:
    print(f"   [ERROR] Failed to load: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
