from PIL import ImageGrab


class ScreenCapture:
    @staticmethod
    def capture_screen(region=None):
        """
        Captures the screen.
        :param region: Tuple (x, y, width, height) or None for full screen.
        :return: PIL Image
        """
        if region:
            # ImageGrab.grab expects (left, top, right, bottom)
            # region is usually (x, y, w, h)
            bbox = (region[0], region[1], region[0] + region[2], region[1] + region[3])
            return ImageGrab.grab(bbox=bbox)
        return ImageGrab.grab()
