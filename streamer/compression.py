import cv2
import numpy as np

class Compressor:
    """
    Handles image compression and decompression.
    
    We use JPEG compression, which is excellent for this use case because it's fast
    and provides a great trade-off between file size and image quality, which is
    adjustable.
    """
    def __init__(self, quality: int = 90):
        """
        Initializes the compressor.
        
        Args:
            quality (int): The JPEG compression quality (1-100). Higher is better quality.
        """
        self.quality = quality
        self.encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.quality]

    def compress(self, frame: np.ndarray) -> bytes:
        """
        Compresses an image frame.
        
        Args:
            frame (np.ndarray): The raw image frame from OpenCV.
            
        Returns:
            bytes: The compressed image data as a byte string.
        """
        result, encimg = cv2.imencode('.jpg', frame, self.encode_param)
        if not result:
            raise RuntimeError("Failed to encode frame to JPEG.")
        return encimg.tobytes()

    def decompress(self, data: bytes) -> np.ndarray:
        """
        Decompresses image data back into a frame.
        
        Args:
            data (bytes): The compressed image data.
            
        Returns:
            np.ndarray: The decompressed image frame.
        """
        img_array = np.frombuffer(data, dtype=np.uint8)
        return cv2.imdecode(img_array, cv2.IMREAD_COLOR)


