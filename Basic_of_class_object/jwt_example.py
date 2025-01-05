from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List
import jwt
from datetime import datetime, timedelta
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")
SECRET_KEY = "supersecret"
ALGORITHM = "HS256"
# Add CORS middleware
origins = [
    "http://127.0.0.1:5500"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Simulated user database
users_db = {
    "user1": {"password": "password123", "roles": ["user"]},
    "admin": {"password": "adminpass", "roles": ["admin", "user"]},
}

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/login")
def login(request: LoginRequest):
    if users_db.get(request.username) and users_db[request.username]["password"] == request.password:
        return {"message": f"Welcome {request.username}!"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/login-jwt")
def login_jwt(request: LoginRequest):
    if users_db.get(request.username) and users_db[request.username]["password"] == request.password:
        token_data = {
            "sub": request.username,
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
        return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/secure-data")
def secure_data(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        return {"message": f"Hello, {username}"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/token")
def token(form_data: OAuth2PasswordRequestForm = Depends()):
    if users_db.get(form_data.username) and users_db[form_data.username]["password"] == form_data.password:
        token_data = {
            "sub": form_data.username,
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
        return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/protected-route")
def protected_route(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"message": f"Access granted for {payload['sub']}"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def role_required(required_roles: List[str], token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_roles = users_db[payload["sub"]]["roles"]
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(status_code=403, detail="Permission denied")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/admin")
async def admin_route(payload: dict = Depends(lambda: role_required(["admin"]))):
    return {"message": "Welcome to the admin area!"}

@app.get("/resource")
async def resource_route(payload: dict = Depends(lambda: role_required(["user"]))):
    return {"message": "Resource accessible"}
