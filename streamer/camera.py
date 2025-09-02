import cv2
import logging_mp as logging

logger = logging.get_logger(__name__)

class Camera:
    """
    A robust wrapper for OpenCV's VideoCapture to handle camera access.
    """
    def __init__(self, camera_index: int = 0):
        """
        Initializes the camera.
        
        Args:
            camera_index (int): The system index of the camera (e.g., 0 for the default webcam).
        
        Raises:
            IOError: If the camera cannot be opened.
        """
        self.camera_index = camera_index
        self.cap = cv2.VideoCapture(self.camera_index)
        
        if not self.cap.isOpened():
            logger.error(f"Could not open camera at index {self.camera_index}.")
            raise IOError(f"Camera at index {self.camera_index} is not available or is in use.")
            
        logger.info(f"Camera {self.camera_index} opened successfully.")

    def capture_frame(self):
        """
        Captures a single frame from the camera.
        
        Returns:
            numpy.ndarray: The captured frame as a NumPy array, or None if the capture failed.
        """
        ret, frame = self.cap.read()
        if not ret:
            logger.warning("Failed to retrieve frame from camera.")
            return None
        return frame

    def release(self):
        """
        Releases the camera resource. This should always be called on exit.
        """
        if self.cap.isOpened():
            self.cap.release()
            logger.info(f"Camera {self.camera_index} released.")


