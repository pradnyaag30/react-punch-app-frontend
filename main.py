from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from couchbase.cluster import Cluster, ClusterOptions
from couchbase.auth import PasswordAuthenticator
from couchbase.exceptions import CouchbaseException
from dotenv import load_dotenv
import os
import uuid
from fastapi.middleware.cors import CORSMiddleware
# from datetime import datetime, timedelta, timezone
 
# ist_offset = timedelta(hours=5, minutes=30)
# ist_time = datetime.now(timezone.utc) + ist_offset
 
from datetime import datetime
import pytz  # <— Make sure you have this installed (pip install pytz)
 
# Get current IST time
ist = pytz.timezone('Asia/Kolkata')
current_ist_time = datetime.now(ist)
 
# Format in IST as string
created_at_ist = current_ist_time.strftime("%d/%m/%Y %H:%M:%S")
# Format: DD/MM/YYYY HH:MM:SS
# created_at = ist_time.strftime("%d/%m/%Y %H:%M:%S")
 
 
load_dotenv()
 
 
 
app = FastAPI(title="Punch In API", version="1.0")
 
 
 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or specify ["http://127.0.0.1:5500"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
# Couchbase setup
try:
    cluster = Cluster(
        os.getenv("COUCHBASE_CONN_STR"),
        ClusterOptions(
            PasswordAuthenticator(
                os.getenv("COUCHBASE_USERNAME"),
                os.getenv("COUCHBASE_PASSWORD")
            )
        )
    )
    bucket = cluster.bucket(os.getenv("COUCHBASE_BUCKET"))
    collection = bucket.scope(os.getenv("COUCHBASE_SCOPE")).collection(os.getenv("COUCHBASE_COLLECTION"))
 
    print("✅ Connected to Couchbase successfully!")
except Exception as e:
    print("❌ Couchbase connection failed:", e)
 
 
# ---------- MODELS ----------
class Punch(BaseModel):
    time: str
    timestamp: str
 
 
# ---------- ROUTES ----------
@app.post("/api/punch")
async def punch_in(punch: Punch):
    """
    Insert a new punch record into Couchbase
    """
    try:
        print("Received punch:", created_at_ist)
        doc_id = f"punch::{uuid.uuid4()}"
        punch_doc = {
            "time": punch.time,
            "timestamp": punch.timestamp,
            "createdAt":  created_at_ist  
        }
 
        collection.insert(doc_id, punch_doc)
        return {"message": "Punch recorded successfully", "id": doc_id}
 
    except CouchbaseException as e:
        raise HTTPException(status_code=500, detail=str(e))
 
 
@app.get("/api/punches")
async def get_punches():
    """
    Retrieve all punch records from Couchbase
    """
    try:
        query_str = f"SELECT META().id, time, timestamp, createdAt FROM `{os.getenv('COUCHBASE_BUCKET')}`.`{os.getenv('COUCHBASE_SCOPE')}`.`{os.getenv('COUCHBASE_COLLECTION')}` ORDER BY createdAt DESC LIMIT 20;"
        result = cluster.query(query_str)
 
        punches = [row for row in result.rows()]
        return {"punches": punches}
 
    except CouchbaseException as e:
        raise HTTPException(status_code=500, detail=str(e))
 
 
