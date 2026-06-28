import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("Missing Supabase credentials in .env")
    exit(1)

# Must use service key to create users via admin api
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

email = "admin@dsrpetrol.com"
password = "Password123!"
full_name = "System Admin"

try:
    print(f"Creating user {email}...")
    # Create user in auth.users
    response = supabase.auth.admin.create_user({
        "email": email,
        "password": password,
        "email_confirm": True
    })
    
    user_id = response.user.id
    print(f"Auth user created with ID: {user_id}")
    
    # Insert into public.users table (this table was created in schema.sql)
    print("Inserting into public.users...")
    supabase.table("users").insert({
        "id": user_id,
        "email": email,
        "full_name": full_name,
        "role": "super_admin",
        "is_active": True
    }).execute()
    
    print("\n✅ User setup complete!")
    print("-" * 30)
    print(f"Email:    {email}")
    print(f"Password: {password}")
    print(f"Role:     super_admin")
    print("-" * 30)

except Exception as e:
    print(f"\n❌ Error creating user: {e}")
    print("If the error says relation 'public.users' does not exist, make sure you ran schema.sql in Supabase SQL Editor!")
