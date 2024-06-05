from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional

from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import asyncio
import json
import asyncpg
import aioredis


app = FastAPI()

class ProfileView(BaseModel):
    viewer_profile_id: int
    viewed_profile_id: int
    timestamp: datetime
    session_id: str

DATABASE_URL = "postgresql://user:password@postgres/mydatabase"
REDIS_URL = "redis://redis:6379"
db_pool = None
kafka_producer = None
kafka_consumer = None

@app.on_event("startup")
async def startup_event():
    global kafka_producer, kafka_consumer, db_pool, redis
    # Replace 'kafka:29092' with your Kafka server address
    kafka_producer = AIOKafkaProducer(bootstrap_servers='kafka:29092')
    await kafka_producer.start()

    kafka_consumer = AIOKafkaConsumer(
        'live_views',
        bootstrap_servers='kafka:29092',
        group_id="fastapi-group"
    )
    await kafka_consumer.start()
    db_pool = await asyncpg.create_pool(DATABASE_URL)
    redis = aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
    asyncio.create_task(consume_messages())

@app.on_event("shutdown")
async def shutdown_event():
    global kafka_producer, kafka_consumer
    await kafka_producer.stop()
    await kafka_consumer.stop()

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


async def increment_all_time_views(profile_id: int):
    async with db_pool.acquire() as connection:
        await connection.execute('''
            UPDATE profiles
            SET all_time_views = all_time_views + 1
            WHERE profile_id = $1
        ''', profile_id)
        print(f"Incremented all_time_views for profile_id: {profile_id}")

async def consume_messages():
    global kafka_consumer
    try:
        async for msg in kafka_consumer:
            view_data = json.loads(msg.value.decode())
            view = ProfileView(**view_data)
            print(f"Consumed from Kafka: {view}")
            await add_profile_view(view)
            await increment_all_time_views(view.viewed_profile_id)
            await increment_live_view_counter(view.viewed_profile_id, view.session_id)
    except Exception as e:
        print(f"Error consuming messages: {e}")

async def increment_live_view_counter(profile_id: int, session_id: str):
    key = f"live_views:{profile_id}:{session_id}"
    await redis.incr(key)
    await redis.expire(key, timedelta(hours=1))
    print(f"Incremented live view counter for key: {key}")



async def add_profile_view(view: ProfileView):
    async with db_pool.acquire() as connection:
        await connection.execute('''
            INSERT INTO profile_views (viewer_profile_id, viewed_profile_id, timestamp, session_id)
            VALUES ($1, $2, $3, $4)
        ''', view.viewer_profile_id, view.viewed_profile_id, view.timestamp, view.session_id)
        print(f"Inserted into profile_views: {view}")

async def increment_all_time_views(profile_id: int):
    async with db_pool.acquire() as connection:
        await connection.execute('''
            UPDATE profiles
            SET all_time_views = all_time_views + 1
            WHERE profile_id = $1
        ''', profile_id)
        print(f"Incremented all_time_views for profile_id: {profile_id}")

@app.get("/profiles/{profileId}/views/live")
async def get_live_views(profileId: int, sessionId: str):
    key = f"live_views:{profileId}:{sessionId}"
    try:
        live_views = await redis.get(key)
        if live_views is None:
            return {"profile_id": profileId, "session_id": sessionId, "live_views": 0}
        return {"profile_id": profileId, "session_id": sessionId, "live_views": int(live_views)}
    except Exception as e:
        print(f"Error retrieving live views: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving live views")


@app.get("/")
def read_root():
    return {"Hello": "World"}
