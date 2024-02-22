import database
from auth import hash_password, verify_password, create_jwt_token, decode_jwt_token
from model import UserCreate
from fastapi import FastAPI, Depends, HTTPException, WebSocketDisconnect, WebSocket
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List
from fastapi.responses import HTMLResponse
from websocket import ConnectionManager
from dotenv import load_dotenv


app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
manager = ConnectionManager()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <h2>Your ID: <span id="ws-id"></span></h2>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var client_id = Date.now()
            document.querySelector("#ws-id").textContent = client_id;
            var ws = new WebSocket(`ws://localhost:8000/chat/ws/${client_id}`);
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port="8000")
    load_dotenv()


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

@app.get("/chat")
async def get_chat():
    return HTMLResponse(html)

@app.websocket("/chat/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"You wrote: {data}", websocket)
            await manager.broadcast(f"Client #{client_id} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left chat")
