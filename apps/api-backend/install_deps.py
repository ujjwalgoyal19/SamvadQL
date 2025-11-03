#!/usr/bin/env python
"""
Quick backend dependency installer for development.
"""

import subprocess
import sys

dependencies = [
    "email-validator==2.2.0",
    "passlib[bcrypt]==1.7.4",
    "python-jose[cryptography]==3.3.0",
    "argon2-cffi==25.1.0",
    "sqlalchemy[asyncio]==2.0.23",
    "asyncpg==0.29.0",
]

print("Installing critical backend dependencies...")
for dep in dependencies:
    print(f"  Installing {dep}...")
    subprocess.run([sys.executable, "-m", "pip", "install", dep, "-q"], check=False)

print("✓ All dependencies installed")
