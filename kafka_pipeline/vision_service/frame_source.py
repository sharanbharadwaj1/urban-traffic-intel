import cv2


class FrameSource:

    def __init__(self, source):

        self.source = source
        self.cap = cv2.VideoCapture(source)

        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open video source: {source}")

    def read(self):

        ret, frame = self.cap.read()

        if not ret:
            return None

        return frame