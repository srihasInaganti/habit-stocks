from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List
from mongo import db
app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello World"}

class PortfolioResponse(BaseModel):
    money: float
    stocks: Dict[str, int]

class LeaderboardEntry(BaseModel):
    user_id: str
    username: str
    stock_value: float

class LeaderboardResponse(BaseModel):
    group_id: str
    leaderboard: List[LeaderboardEntry]

class GroupCreateRequest(BaseModel):
    name: str

class JoinGroupRequest(BaseModel):
    user_id: str

#fetch the user’s current money and owned stocks
@app.get("/users/{user_id}/portfolio", response_model=PortfolioResponse)
async def get_portfolio(user_id: str):
    user = db.users.find_one({"_id": user_id})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    portfolio = {
        "money": user.get("money", 0.0),
        "stocks": user.get("stocks", {})
    }
    
    return portfolio
 
 #fetch all habits and stock prices
@app.get("/groups/{group_id}/dashboard")
def get_group_dashboard(group_id: str):
    habits = list(db.habits.find({"group_id": group_id}))

    if not habits:
        raise HTTPException(status_code=404, detail="No habits found for this group")

    #convert objectIDs to strings
    for i in habits:
        i["_id"] = str(i["_id"])

    return {
        "group_id": group_id,
        "total_habits": len(habits),
        "habits": habits
    }

#fetch group leaderboard
@app.get("/groups/{group_id}/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(group_id: str):
    users = list(db.users.find({"group_id": group_id}))
    
    if not users:
        raise HTTPException(status_code=404, detail="No users found for this group")
    
    leaderboard = []
    for user in users:
        stock_value = user.get("money", 0.0)
        stocks = user.get("stocks", {})
        #each stock counts as 1 point per share --> we need to change this later
        stock_value += sum(stocks.values())
        
        leaderboard.append({
            "user_id": str(user["_id"]),
            "username": user.get("username", "Unknown"),
            "stock_value": stock_value
        })

    leaderboard.sort(key=lambda x: x["stock_value"], reverse=True)
    
    return {
        "group_id": group_id,
        "leaderboard": leaderboard
    }

#creating a new group
@app.post("/groups")
async def create_group(group: GroupCreateRequest):
    new_group = {
        "name": group.name,
        "description": group.description or "",
        "created_at": datetime.utcnow()
    }
    result = db.groups.insert_one(new_group)
    #converts objectID to a string
    new_group["_id"] = str(result.inserted_id) 
    
    return {
        "message": "Group created successfully!",
        "group": new_group
    }

#joining an existing group
@app.post("/groups/{group_id}/join")
async def join_group(group_id: str, request: JoinGroupRequest):
    group = db.groups.find_one({"_id": group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found :(")
    
    user = db.users.find_one({"_id": request.user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found :(")
    
    db.users.update_one(
        {"_id": request.user_id},
        {"$set": {"group_id": group_id}} #sets the user id to the group's id
    )
    
    return {"message": f"User {request.user_id} joined group {group_id} successfully!"}