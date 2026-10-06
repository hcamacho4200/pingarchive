"""Various request context utilities"""

import uuid
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from time import time

from api.schema.api_response_schema import MetaAPIData


@dataclass
class RequestMeta:
    """Request metadata"""

    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    start_time: float = field(default_factory=time)
    end_time: float | None = None

    def finish(self):
        """Finish the request"""
        self.end_time = time()

    @property
    def duration_ms(self) -> float | None:
        """Request duration in milliseconds"""
        if self.end_time is None:
            return None
        return round((self.end_time - self.start_time) * 1000, 2)


@contextmanager
def request_meta_context() -> Generator[RequestMeta]:
    """Request metadata context manager"""
    meta = RequestMeta()
    yield meta
    meta.finish()


def build_meta(meta: RequestMeta, status: str = "success", status_code: int = 200) -> MetaAPIData:
    """Build request metadata"""
    return MetaAPIData(
        **{
            "status": status,
            "request_id": meta.request_id,
            "status_code": status_code,
            "start_time_epoch": meta.start_time,
            "end_time_epoch": meta.end_time,
            "duration_ms": meta.duration_ms,
        }
    )
