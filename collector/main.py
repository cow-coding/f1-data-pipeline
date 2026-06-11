import logging
import os
from asyncio import create_task
from contextlib import asynccontextmanager

from logger import setup_logger

setup_logger()
logger = logging.getLogger(__name__)

os.environ['ROOT_DIR'] = os.getcwd()

from fastapi import FastAPI

from buffer.buffer import event_buffer, check_flush_loop
from model.event import Event
from preprocessor.preprocessor import event_preprocessor


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = create_task(check_flush_loop())
    yield
    task.cancel()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/events")
async def receive_event(body: Event):
    logger.info(f"Received event\n {body}")
    refined_event = event_preprocessor.run(body)
    logger.info(f"Refined event\n {refined_event}")
    await event_buffer.insert(refined_event)
    return {"status": "received"}
