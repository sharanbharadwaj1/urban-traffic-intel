from dataclasses import dataclass
from datetime import datetime, timezone

import cv2
import numpy as np

from app.core.config import Settings


@dataclass
class FramePacket:
    frame_index: int
    timestamp: datetime
    frame: np.ndarray


class FramePipeline:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def should_process(self, frame_index: int) -> bool:
        return frame_index % self.settings.frame_skip == 0

    def preprocess(self, frame_index: int, frame: np.ndarray) -> FramePacket:
        processed = frame
        if self.settings.frame_resize_width > 0 and frame.shape[1] > self.settings.frame_resize_width:
            ratio = self.settings.frame_resize_width / frame.shape[1]
            processed = cv2.resize(frame, None, fx=ratio, fy=ratio, interpolation=cv2.INTER_AREA)

        return FramePacket(
            frame_index=frame_index,
            timestamp=datetime.now(timezone.utc),
            frame=processed,
        )
