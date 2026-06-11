import asyncio
import json
import logging
import os
import pathlib
import time

from s3fs import S3FileSystem

logger = logging.getLogger(__name__)

import pyarrow as pa
import pyarrow.parquet as pq
import datetime
from typing import List

from model.event import RefinedEvent

MINIO_BUCKET = os.getenv("MINIO_BUCKET", "f1-raw")  # f1-data-pipeline path
DEAD_LETTER_PATH = os.path.join(os.getenv("ROOT_DIR"), "data/dead_letter")
FLUSH_DATA_ROW_SIZE = 100
BACKOFF_COUNT = 3


class Buffer:
    event_list: List[RefinedEvent]
    last_flushed: datetime.datetime
    last_flushed_hour: int
    buffer_lock: asyncio.Lock
    fs: S3FileSystem

    def __init__(self):
        self.buffer_lock = asyncio.Lock()
        self.event_list = []
        self.last_flushed = datetime.datetime.now(datetime.UTC)
        self.last_flushed_hour = self.last_flushed.hour
        self.fs = S3FileSystem(
            endpoint_url=os.getenv("MINIO_ENDPOINT"),
            key=os.getenv("MINIO_ACCESS_KEY"),
            secret=os.getenv("MINIO_SECRET_KEY"),
        )

    def __serialize(self, events: List[RefinedEvent]):
        result = []
        for event in events:
            e = event.model_dump()
            e['payload'] = json.dumps(e['payload'])
            e['event_id'] = str(e['event_id'])
            result.append(e)

        return result

    async def insert(self, event: RefinedEvent):
        async with self.buffer_lock:
            self.event_list.append(event)

    def __check_dead_letter_files(self, with_write=False):
        if not os.path.exists(DEAD_LETTER_PATH):
            os.makedirs(DEAD_LETTER_PATH)

        if len(os.listdir(DEAD_LETTER_PATH)) != 0:
            if with_write:
                dead_letter_events = []
                for file in os.listdir(DEAD_LETTER_PATH):
                    with open(os.path.join(DEAD_LETTER_PATH, file), 'r') as f:
                        dead_letter_events.extend([RefinedEvent(**e) for e in json.load(f)])
                self.event_list.extend(dead_letter_events)
                return True
            else:
                return True
        return False

    def __file_write(self):
        schema = pa.schema([
            pa.field("event_id", pa.string()),
            pa.field("event_type", pa.string()),
            pa.field("emitted_at", pa.timestamp('us')),
            pa.field("date", pa.date32()),
            pa.field("hour", pa.int32()),
            pa.field("payload", pa.string()),
        ])
        table = pa.Table.from_pylist(self.__serialize(self.event_list), schema)
        root_path = f"{MINIO_BUCKET}/raw"
        timestamp = int(datetime.datetime.now(datetime.UTC).timestamp())
        pq.write_to_dataset(
            table,
            filesystem=self.fs,
            root_path=root_path,
            partition_cols=["event_type", "date", "hour"],
            basename_template=f"part-{timestamp}-{{i}}.parquet"
        )
        self.last_flushed = datetime.datetime.now(datetime.UTC)
        self.last_flushed_hour = self.last_flushed.hour
        logger.info("flushed %d events to parquet", len(self.event_list))
        self.event_list = []
        for file in os.listdir(DEAD_LETTER_PATH):
            os.remove(os.path.join(DEAD_LETTER_PATH, file))

    async def write(self):
        self.__check_dead_letter_files(with_write=True)
        for backoff in range(BACKOFF_COUNT):
            logger.info(f"[{backoff + 1}] Write Files Attempt")
            try:
                self.__file_write()
                break
            except Exception as e:
                logger.error(f"[{backoff + 1}] Write Files Failed: error={e}")
                logger.error(f"Now waiting {backoff + 1} second")
                await asyncio.sleep(backoff + 1)
        else:
            # 최종 실패시 DEAD_LETTER_PATH 에 json으로 이벤트 로그 저장
            timestamp = int(datetime.datetime.now(datetime.UTC).timestamp())
            with open(os.path.join(DEAD_LETTER_PATH, str(timestamp)), 'w') as f:
                json.dump([e.model_dump(mode='json') for e in self.event_list], f)

    async def check_flush_condition(self):
        async with self.buffer_lock:
            logger.info("buffer size=%d", len(self.event_list))
            if len(self.event_list) >= FLUSH_DATA_ROW_SIZE:
                await self.write()
                return

            if datetime.datetime.now(datetime.UTC).hour != self.last_flushed_hour:
                await self.write()
                return


event_buffer = Buffer()


async def check_flush_loop():
    while True:
        try:
            logger.info("flush loop tick")
            await event_buffer.check_flush_condition()
        except Exception as e:
            logger.error("flush loop error: %s", e)
        await asyncio.sleep(1)
