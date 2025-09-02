# Encrypted UDP JPEG Stream

A modular Python package designed for securely streaming compressed camera footage over a network using UDP. This project prioritizes speed and efficiency for real-time video transmission, incorporating encryption to ensure data confidentiality and integrity.

## Features

- **Real-time Camera Capture**: Utilizes OpenCV to capture frames from a specified camera device.
- **Efficient JPEG Compression**: Compresses video frames into JPEG format, balancing quality and file size for network transmission.
- **Symmetric Encryption**: Employs the `cryptography` library (Fernet) for authenticated encryption, ensuring data privacy and detecting tampering.
- **UDP-based Streaming**: Leverages UDP for low-latency, high-throughput streaming, suitable for real-time video where occasional packet loss is acceptable.
- **Packetization**: Automatically splits large frames into smaller UDP packets and reassembles them on the receiver side.
- **Key Management**: Provides a utility to generate and save encryption keys securely.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/MertKures/encrypted_udp_jpeg_stream.git
    cd encrypted_udp_jpeg_stream
    ```

2.  **Create a secret key**
    ```bash
    uv run streamer/security.py
    ```

3.  **Start sender**
    ```bash
    uv run __main__.py localhost 5555
    ```

4.  **Start receiver**
    ```bash
    uv run receiver.py localhost 5555
    ```

## Project Structure

-   `receiver.py`: The script responsible for receiving, decrypting, decompressing, and displaying the video stream.
-   `setup.py`: Package installation and dependency management.
-   `__main__.py`: The core logic for streaming (capture, compress, encrypt, send).
-   `streamer/`:
    -   `camera.py`: Handles video capture from the camera.
    -   `compression.py`: Manages JPEG compression and decompression. 
    -   `network.py`: Implements UDP sending and receiving, including packet fragmentation and reassembly.
    -   `security.py`: Provides encryption and decryption functionalities using Fernet.

## Dependencies

The project relies on the following Python libraries, managed via uv:

-   `opencv-python`
-   `numpy`
-   `cryptography`

## Contributing

Contributions are welcome! Please feel free to open issues or submit pull requests.

## License

This project is licensed under the MIT License.
