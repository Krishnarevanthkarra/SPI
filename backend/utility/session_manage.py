from ..database import get_db
from ..settings import Collections
from ..schemas import Session
from datetime import datetime, timezone
from pymongo.asynchronous.database import AsyncDatabase


async def manageSessions(
    email,
    devicename: str,
    collection_name: Collections.USER | Collections.ORGANIZATION,
    db: AsyncDatabase,
):
    collection = db.get_collection(collection_name)
    user = await collection.find_one({"email": email})
    session_collection = db.get_collection(Collections.SESSIONS)
    existing_sessions = await session_collection.find(
        {"userid": str(user.get("_id"))}
    ).to_list(length=None)
    if user.get("subscription").get("devicesallowed") == len(existing_sessions):
        sessions = sorted(existing_sessions, key=lambda session: session["last_used"])
        await session_collection.delete_one(sessions[0])
    curr_session = Session(
        userid=str(user.get("_id")),
        devicename=devicename,
        createdAt=datetime.now(timezone.utc),
        last_used=datetime.now(timezone.utc),
    )
    new_session = await session_collection.insert_one(
        curr_session.model_dump(by_alias=True)
    )
    return str(new_session.inserted_id)
