from pymongo import AsyncMongoClient
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from .settings import settings, Collections
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


@asynccontextmanager
async def db_connection(app: FastAPI):
    app.state.client = AsyncMongoClient(settings.database_uri)
    app.state.database = app.state.client.get_database("dev")

    ping = await app.state.database.command("ping")
    if int(ping["ok"]) != 1:
        raise Exception("Problem Connectiong to DB")
    else:
        logging.info("Connected to database cluster.")
    await app.state.database.get_collection(Collections.USER).create_index("email")
    await app.state.database.get_collection(Collections.ORGANIZATION).create_index(
        "email"
    )
    await app.state.database.get_collection(Collections.AHP_SHEETS).create_index(
        "userid"
    )
    await app.state.database.get_collection(Collections.BOARDS).create_index("userid")
    yield

    await app.state.client.close()
    logging.info("Connection is closed.")


def get_db(request: Request):
    return request.app.state.database
