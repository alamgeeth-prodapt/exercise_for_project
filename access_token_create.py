from jose import jwt 
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
load_dotenv()

KEY = os.getenv("KEY")
ALGORITHM = "HS256"

def create_access_token(username: str):
    expire = datetime.utcnow() + timedelta(minutes=30)

    payload = {
        "sub" : username,
        "exp" : expire
    }

    return jwt.encode(payload,KEY, algorithm=ALGORITHM)



