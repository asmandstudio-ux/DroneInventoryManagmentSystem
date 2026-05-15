import asyncio
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import async_session_maker
from app.models.user import User
from app.core.security import get_password_hash
from app.core.config import settings

async def create_superuser():
    print("--- Creating Super Admin User ---")
    
    username = "finsun2020"
    password = "AestheticS68742!"
    email = "finsun2020@droneims.local"
    
    async with async_session_maker() as session:
        # Check if user exists
        result = await session.execute(
            User.__table__.select().where(User.__table__.c.username == username)
        )
        user = result.fetchone()
        
        if user:
            print(f"User '{username}' already exists. Updating password...")
            hashed_pw = get_password_hash(password)
            await session.execute(
                User.__table__.update()
                .where(User.__table__.c.username == username)
                .values(password=hashed_pw, is_superuser=True, is_active=True)
            )
            await session.commit()
            print("Password updated successfully.")
        else:
            print(f"Creating new user: {username}...")
            hashed_pw = get_password_hash(password)
            
            new_user = User(
                username=username,
                email=email,
                password=hashed_pw,
                is_superuser=True,
                is_active=True,
                role="admin" # Assuming role column exists, adjust if needed
            )
            
            session.add(new_user)
            await session.commit()
            print("Super Admin user created successfully!")
            
    print("---------------------------------")
    print(f"Login Credentials:")
    print(f"Username: {username}")
    print(f"Password: {password}")
    print("---------------------------------")

if __name__ == "__main__":
    try:
        asyncio.run(create_superuser())
    except Exception as e:
        print(f"Error creating user: {e}")
        sys.exit(1)
