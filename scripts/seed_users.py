#!/usr/bin/env python3
"""
Seed Users Script
-----------------
Creates five example users, one for each Access Matrix level (1-5).
Run:  python scripts/seed_users.py
"""

import asyncio
from pathlib import Path
import sys
from sqlalchemy import select, delete

# Ensure project root on path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.database import async_session_factory, engine
from app.models import User, UserAccessLevel, BankDocument, BankDocumentV2, AuditLog
from app.security import get_password_hash, verify_password

EXAMPLE_USERS = [
    {"username": "public_user", "email": "public@example.com", "password": "public123", "access_level": UserAccessLevel.PUBLIC, "role": "Public Viewer"},
    {"username": "internal_user", "email": "internal@example.com", "password": "internal123", "access_level": UserAccessLevel.INTERNAL, "role": "Internal Staff"},
    {"username": "confidential_user", "email": "confidential@example.com", "password": "confidential123", "access_level": UserAccessLevel.CONFIDENTIAL, "role": "Risk Analyst"},
    {"username": "restricted_user", "email": "restricted@example.com", "password": "restricted123", "access_level": UserAccessLevel.RESTRICTED, "role": "Compliance Officer"},
    {"username": "executive_user", "email": "executive@example.com", "password": "executive123", "access_level": UserAccessLevel.EXECUTIVE, "role": "Executive"},
]


async def seed_users():
    async with async_session_factory() as session:
        # Ensure tables exist
        async with engine.begin() as conn:
            await conn.run_sync(lambda conn: None)

        # 1) Remove referencing records to avoid FK violations
        await session.execute(delete(BankDocumentV2))
        await session.execute(delete(BankDocument))
        await session.execute(delete(AuditLog))
        await session.execute(delete(User))
        await session.commit()
        print("🗑️  Cleared existing users table")

        # 2) Insert fresh users with hashed passwords
        for u in EXAMPLE_USERS:
            user = User(
                username=u["username"],
                email=u["email"],
                password_hash=get_password_hash(u["password"]),
                access_level=u["access_level"],
                role=u["role"],
            )
            session.add(user)
            print(f"➕ Added user '{u['username']}' (level {u['access_level']})")

        await session.commit()
        print("✅ Seeding completed.")

        # 3) Verify login credentials in-memory using hashing
        for u in EXAMPLE_USERS:
            stmt = select(User).where(User.username == u["username"])
            result = await session.execute(stmt)
            user: User = result.scalar_one()
            if verify_password(u["password"], user.password_hash):
                print(f"🔐 Verified hash for user '{u['username']}' -> OK")
            else:
                print(f"❌ Hash verification failed for user '{u['username']}'")


if __name__ == "__main__":
    asyncio.run(seed_users()) 