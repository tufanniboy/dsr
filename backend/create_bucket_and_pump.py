import asyncio
import os
import sys

# Add parent dir to path so we can import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.supabase import get_supabase_client

def setup():
    client = get_supabase_client()
    
    # Create bucket
    try:
        client.storage.create_bucket("dsr-images", {"public": False})
        print("Bucket 'dsr-images' created.")
    except Exception as e:
        print(f"Bucket creation error (might already exist): {e}")

    # Create a default pump if none exists
    pumps = client.table("petrol_pumps").select("*").execute()
    if not pumps.data:
        print("Creating default petrol pump...")
        pump_res = client.table("petrol_pumps").insert({
            "name": "Default Pump",
            "code": "DP01"
        }).execute()
        pump_id = pump_res.data[0]["id"]
    else:
        pump_id = pumps.data[0]["id"]
        print(f"Using existing pump {pump_id}")

    # Assign pump_id to all users who don't have one
    users = client.table("users").select("*").is_("pump_id", "null").execute()
    for user in users.data:
        client.table("users").update({"pump_id": pump_id}).eq("id", user["id"]).execute()
        print(f"Assigned pump to user {user['email']}")

if __name__ == "__main__":
    setup()
