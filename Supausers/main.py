import uuid
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client
import logging
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins, replace with specific domains if needed
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

load_dotenv()
# Supabase setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class UserCreateRequest(BaseModel):
    email: str
    password: str
    full_name: str
    phone_number: str | None = None
    suscriptoruuid: str | None = None
    puesto_uuid: str | None = None
    rfc: str | None = None
    status_code: int | None = None

@app.post("/create-user/")
async def create_user(user: UserCreateRequest):
    try:
        # Step 1: Create user in auth.users
        auth_response = supabase.auth.admin.create_user({
            "email": user.email,
            "password": user.password,
            "user_metadata": {
                "full_name": user.full_name,
                "phone_number": user.phone_number,
                "suscriptoruuid": user.suscriptoruuid,
                "puesto_uuid": user.puesto_uuid,
                "rfc":user.rfc,
                "status_code": user.status_code

            }
        })

        if not auth_response.user:
            logger.error("User creation failed: %s", auth_response)
            raise HTTPException(status_code=400, detail="User creation failed")

        user_id = auth_response.user.id

        # Step 2: Create profile in public.profiles
        profile_data = {
            "id": user_id,  # Same ID as auth.users
            "suscriptoruuid": user.suscriptoruuid,
            "full_name": user.full_name,
            "phone": user.phone_number,
            "puesto_uuid": user.puesto_uuid,
            "rfc":user.rfc,
            "status_code": user.status_code,
            "username": user.email,
            "email": user.email,
        }

        profile_response = supabase.table("profiles").insert(profile_data).execute()

        if not profile_response.data:  # Check if profile creation succeeded
            logger.error("Profile creation failed: %s", profile_response)
            raise HTTPException(status_code=400, detail="Profile creation failed")

        return {
            "success": True,
            "user_id": user_id,
            "message": "User and profile created successfully"
        }

    except Exception as e:
        logger.error("Internal server error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
