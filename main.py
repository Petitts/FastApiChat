import database
from auth import hash_password, verify_password, create_jwt_token, decode_jwt_token
from model import UserCreate
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port="8000")


@app.post("/register")
async def register(user: UserCreate):
    # Sprawdz czy user istnieje
    existing_user = await database.db.users.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exist")
    
    # Zapisz nowego usera
    user_data = user.dict()
    user_data["password"] = hash_password(user_data["password"])
    user_data['role'] = 'user'
    await database.db.users.insert_one(user_data)

    return {"message:": "User registered successfully"}

@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await database.db.users.find_one({"username": form_data.username})
    if not user or not verify_password(form_data.password, user['password']):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    if user['role'] not in ["admin", "user"]:
        raise HTTPException(status_code=400, detail="Invalid role")

    # Wygeneruj token JWT
    token_data = {"sub": user["username"], "role": user['role']}
    token = create_jwt_token(token_data)

    return {"access_token": token, "token_type": "bearer"}

@app.get("/users")
async def get_users(token: str = Depends(oauth2_scheme)):
    user = decode_jwt_token(token)
    if user['role'] == "admin":
        users = await database.db.users.find({},{'_id': 0}).to_list(1000)
        
        return users
    else:
        raise HTTPException(status_code=403, detail="Permission denied")
