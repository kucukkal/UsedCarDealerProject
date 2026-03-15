# seed_users.py
import os
from app.database import SessionLocal
from app import models
from app.routers.auth import get_password_hash

# List of users to seed
USERS_TO_CREATE = [
    # ----- Global-Level Users -----
    {
        "username": "admin",
        "password": "admin123!",
        "role": "Admin",
        "location": "HQ"
    },
    {
        "username": "accountant",
        "password": "account123!",
        "role": "Finance",
        "location": "HQ"
    },

    # ----- Location A Users -----
    {"username": "pr_user_A", "password": "prA123!", "role": "PR", "location": "Denver"},
    {"username": "service_rep_A", "password": "serviceA123!", "role": "ServiceRep", "location": "Denver"},
    {"username": "sales_rep_A", "password": "salesA123!", "role": "SalesRep", "location": "Denver"},
    {"username": "buyer_rep_A", "password": "buyerA123!", "role": "BuyerRep", "location": "Denver"},

    # ----- Location B Users -----
    {"username": "pr_user_B", "password": "prB123!", "role": "PR", "location": "Rockville"},
    {"username": "service_rep_B", "password": "serviceB123", "role": "ServiceRep", "location": "Rockville"},
    {"username": "sales_rep_B", "password": "salesB123", "role": "SalesRep", "location": "Rockville"},
    {"username": "buyer_rep_B", "password": "buyerB123", "role": "BuyerRep", "location": "Rockville"},
]


def seed_users():
    db = SessionLocal()
    created = 0
    skipped = 0

    for user in USERS_TO_CREATE:
        # Check if user exists
        existing = db.query(models.User).filter(models.User.username == user["username"]).first()

        if existing:
            print(f"Skipping (already exists): {user['username']}")
            skipped += 1
            continue

        # Create new user
        hashed = get_password_hash(user["password"])

        db_user = models.User(
            username=user["username"],
            password_hash=hashed,
            role=user["role"],
            location=user["location"]
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        print(f"Created user: {user['username']}")
        created += 1

    db.close()

    print("\n✨ DONE SEEDING USERS ✨")
    print(f"Created: {created}")
    print(f"Skipped (already exists): {skipped}")


if __name__ == "__main__":
    seed_users()
