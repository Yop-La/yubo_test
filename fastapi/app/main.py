from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from aiokafka import AIOKafkaProducer
import asyncio

app = FastAPI()


class Profile(BaseModel):
    profile_id: Optional[int] = None  # Optional in case of POST requests where ID is auto-generated
    profile_name: str
    all_time_views: int

class ProfileView(BaseModel):
    view_id: Optional[int] = None  # Optional as it's auto-generated
    viewer_profile_id: int
    viewed_profile_id: int
    timestamp: datetime
    session_id: str



kafka_producer = None

@app.on_event("startup")
async def startup_event():
    global kafka_producer
    # Replace 'localhost:9092' with your Kafka server address
    kafka_producer = AIOKafkaProducer(bootstrap_servers='kafka:29092')
    await kafka_producer.start()

@app.on_event("shutdown")
async def shutdown_event():
    global kafka_producer
    await kafka_producer.stop()

@app.post("/views")
async def record_view(view: ProfileView):
    try:
        await send_to_kafka(view)
        return {"message": "View recorded", "data": view}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def send_to_kafka(view: ProfileView):
    await kafka_producer.send_and_wait("live_views", view.json().encode())
    print(f"Sent to Kafka: {view.json()}")

@app.get("/")
def read_root():
    return {"Hello": "World"}