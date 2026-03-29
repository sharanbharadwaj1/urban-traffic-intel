import cv2

class FrameReader:

    def __init__(self, video_path, frame_skip):
        self.cap = cv2.VideoCapture(video_path)
        self.frame_skip = frame_skip
        self.frame_count = 0

    def read(self):

        while True:
            ret, frame = self.cap.read()

            if not ret:
                break

            self.frame_count += 1

            if self.frame_count % self.frame_skip != 0:
                continue

            yield self.frame_count, frame