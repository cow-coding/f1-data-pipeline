import uuid
from typing import Dict

from pydantic import UUID4

from model.event import Event, RefinedEvent


class Preprocessor:

    @staticmethod
    def __generate_event_id() -> UUID4:
        return uuid.uuid4()

    @staticmethod
    def __process_time(event: Dict) -> Dict:
        emitted_time = event['emitted_at']
        event['date'] = emitted_time.date()
        event['hour'] = emitted_time.hour
        return event

    def run(self, event: Event) -> RefinedEvent:
        data = event.model_dump()
        time_data = self.__process_time(data)
        event_id = self.__generate_event_id()
        return RefinedEvent(
            **time_data,
            event_id=event_id
        )


event_preprocessor = Preprocessor()
