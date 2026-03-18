import easyocr


class OCRReader:

    def __init__(self):

        self.reader = easyocr.Reader(['en'])

    def read_plate(self, image):

        results = self.reader.readtext(image)

        if not results:
            return None

        text = results[0][1]

        return text