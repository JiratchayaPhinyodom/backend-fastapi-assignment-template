from fastapi import FastAPI, HTTPException, Body
from datetime import date, datetime
from pydantic import BaseModel
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import urllib

load_dotenv(".env")

user = os.getenv("username")
password = urllib.parse.quote(os.getenv("password"))
client = MongoClient(f"mongodb://{user}:{urllib.parse.quote(password)}@mongo.exceed19.online:8443/?authMechanism=DEFAULT")

# DATABASE_NAME = "hotel"
# COLLECTION_NAME = "reservation"
DATABASE_NAME = "exceed05"
COLLECTION_NAME = "reservation"
# MONGO_DB_URL = "mongodb://localhost"
# MONGO_DB_PORT = 27017


class Reservation(BaseModel):
    name : str
    start_date: date
    end_date: date
    room_id: int


# client = MongoClient(f"{MONGO_DB_URL}:{MONGO_DB_PORT}")

db = client[DATABASE_NAME]

collection = db[COLLECTION_NAME]

app = FastAPI()


def room_avaliable(room_id: int, start_date: str, end_date: str):
    query={"room_id": room_id,
           "$or": 
                [{"$and": [{"start_date": {"$lte": start_date}}, {"end_date": {"$gte": start_date}}]},
                 {"$and": [{"start_date": {"$lte": end_date}}, {"end_date": {"$gte": end_date}}]},
                 {"$and": [{"start_date": {"$gte": start_date}}, {"end_date": {"$lte": end_date}}]}]
            }
    
    result = collection.find(query, {"_id": 0})
    list_cursor = list(result)

    return not len(list_cursor) > 0

@app.get("/")
def get_show():
    return {"name": "Hellotest"}

@app.get("/reservation/by-name/{name}")
def get_reservation_by_name(name:str):
    return {"result": list(collection.find({"result":name}, {"_id":False}))}

@app.get("/reservation/by-room/{room_id}")
def get_reservation_by_room(room_id: int):
    if room_id > 0 and room_id <= 10:
        return {"result":list(collection.find({"result":room_id}, {"_id":False}))}
    else:
        raise HTTPException(status_code=400, detail="400 Bad Request.The result was unsuccessful.")

@app.post("/reservation")
def reserve(reservation : Reservation):
    if reservation.room_id not in range(1, 11) :
        raise HTTPException(status_code=400)
    if reservation.start_date > reservation.end_date:
        raise HTTPException(status_code=400)
    if not room_avaliable(reservation.room_id, str(reservation.start_date), str(reservation.end_date)):
        raise HTTPException(status_code=400)
    collection.insert_one({"name": reservation.name, 
                           "start_date": reservation.start_date.strftime("%Y-%m-%d"), 
                           "end_date": reservation.end_date.strftime("%Y-%m-%d"), 
                           "room_id": reservation.room_id})

@app.put("/reservation/update")
def update_reservation(reservation: Reservation, new_start_date: date = Body(), new_end_date: date = Body()):
    if new_start_date > new_end_date:
        raise HTTPException(400)
    if not room_avaliable(reservation.room_id, str(new_start_date), str(new_end_date)):
        raise HTTPException(400)
    collection.update_one({"name": reservation.name,
                           "room_id": reservation.room_id},
                          update={"$set": {"start_date": new_start_date.isoformat(),
                                           "end_date": new_end_date.isoformat()}})

@app.delete("/reservation/delete")
def cancel_reservation(reservation: Reservation):
    collection.delete_one({"name":reservation.name})