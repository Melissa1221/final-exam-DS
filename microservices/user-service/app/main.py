from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import uuid
import uvicorn
import os

app = FastAPI(title="User Service", description="microservicio para gestión de usuarios", version="1.0.0")

# modelos de datos
class User(BaseModel):
    id: str = None
    name: str
    email: str  
    age: int

class UserCreate(BaseModel):
    name: str
    email: str
    age: int

# almacenamiento en memoria
users_db: Dict[str, User] = {}

@app.get("/health")
async def health_check():
    """health check"""
    return {"status": "healthy", "service": "user-service"}

@app.post("/users", response_model=User)
async def create_user(user_data: UserCreate):
    """crear usuario"""
    user_id = str(uuid.uuid4())
    user = User(id=user_id, **user_data.dict())
    users_db[user_id] = user
    return user

@app.get("/users", response_model=List[User])
async def list_users():
    """listar usuarios"""
    return list(users_db.values())

@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: str):
    """obtener usuario específico"""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return users_db[user_id]

@app.delete("/users/{user_id}")
async def delete_user(user_id: str):
    """eliminar usuario"""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    del users_db[user_id]
    return {"message": f"User {user_id} deleted successfully"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port) 