from datetime import datetime, timezone
from flask import Flask, request
from dotenv import load_dotenv
import os, psycopg2


CREATE_ROOMS_TABLE = (
    "CREATE TABLE IF NOT EXISTS rooms (id SERIAL PRIMARY KEY,name Text);"
)

CREATE_TEMPS_TABLE = """CREATE TABLE IF NOT EXISTS temperatures (room_id INTEGER, temperature REAL, 
date timestamp, FOREIGN KEY (room_id) REFERENCES rooms (id) ON DELETE CASCADE);"""

INSERT_ROOM_RETURN_ID = "INSERT INTO rooms (name) VALUES (%s) RETURNING id;"

INSERT_TEMP = "INSERT INTO temperatures (room_id, temperature, date) VALUES (%s, %s, %s);"

GLOBAL_NUMBER_OF_ROOMS = "SELECT COUNT(DISTINCT DATE(date)) AS days FROM temperatures;"

GLOBAL_AVG = "SELECT AVG(temperature) as average FROM temperatures;"

load_dotenv()
app = Flask(__name__)
url = os.getenv("DATABASE_URL")

conn = psycopg2.connect(url)
with conn:
    with conn.cursor() as cur:
        cur.execute(CREATE_ROOMS_TABLE)
        cur.execute(CREATE_TEMPS_TABLE)


@app.post("/api/room")
def create_room():
    data = request.get_json()
    name = data["name"]

    with conn:
        with conn.cursor() as cur:
            cur.execute(INSERT_ROOM_RETURN_ID, (name,))
            room_id = cur.fetchone()[0]
            conn.commit()

    return {"id": room_id, "message": f"Room {name} created."}, 201


@app.post("/api/temperature")
def add_temp():
    data = request.get_json()
    temperature = data["temperature"]
    room_id = data["room"]

    try:
        date = datetime.strptime(data["date"], "%m-%d-%Y %H:%M:%S")
    except KeyError:
        date = datetime.now(timezone.utc)

    with conn:
        with conn.cursor() as cur:
            cur.execute(CREATE_TEMPS_TABLE)
            cur.execute(INSERT_TEMP, (room_id, temperature, date))
            conn.commit()
    return {"message": "Temperature added."}, 201


@app.get("/api/average")
def get_global_avg():
    with conn:
        with conn.cursor() as cur:
            cur.execute(GLOBAL_AVG)g
            average = cur.fetchone()[0]
            cur.execute(GLOBAL_NUMBER_OF_ROOMS)
            days = cur.fetchone()[0]
            conn.commit()

    return {"average": round(average, 2), "days": days}


@app.get("/api/rooms")
def get_rooms():
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM rooms")
            rooms = cur.fetchall()
            conn.commit()

    return {"rooms": rooms, "message": "Rooms fetched."}

