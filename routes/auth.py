from fastapi import APIRouter,Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from database import get_db, admin
from sqlalchemy.orm import Session
from schemas import LoginRequest, LoginResponse
from admin_create import hash_passowrd, verify_password
from access_token_create import create_access_token
from fastapi import HTTPException
import os
from dotenv import load_dotenv
from jose import jwt, JWTError

load_dotenv()

key = os.getenv("KEY")
algo = "HS256"
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/login",response_model=LoginResponse)
def login(req: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    query = db.query(admin).filter(admin.username==req.username).first()

    if not query:
        raise HTTPException(401)

    res = verify_password(req.password,query.password)

    if not res:
        raise HTTPException(401)
    token = create_access_token(query.username)

    return LoginResponse(
        access_token=token,
        token_type="bearer"
    )

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(
            token,
            key,
            algorithms=[algo]
        )

        username = payload.get("sub")

        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        return username

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )
