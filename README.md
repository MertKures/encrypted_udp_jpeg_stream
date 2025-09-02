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

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install the package and its dependencies:**
    ```bash
    pip install .
    ```

## Usage

### 1. Generate an Encryption Key

A secret key is required for encryption and decryption. Generate one using the provided utility:

```bash
generate-stream-key
```
This will create a `secret.key` file in your project root. **Share this file securely with your receiver.**

### 2. Start the Streamer (Sender)

Run the `stream-camera` command, specifying the receiver's IP address and port, along with the path to your encryption key.

```bash
stream-camera <receiver_ip_address> <receiver_port> --key_path secret.key --camera_index 0 --quality 90
```

-   `<receiver_ip_address>`: The IP address of the machine running the receiver.
-   `<receiver_port>`: The port on which the receiver is listening.
-   `--key_path`: (Optional) Path to your encryption key file (default: `secret.key`).
-   `--camera_index`: (Optional) The index of the camera to use (default: `0`).
-   `--quality`: (Optional) JPEG compression quality (1-100, default: `90`).

### 3. Start the Receiver

Run the `receiver.py` script, specifying the IP address to listen on and the port, along with the encryption key.

```bash
python receiver.py <listen_ip_address> <listen_port> --key_path secret.key
```

-   `<listen_ip_address>`: The IP address the receiver should listen on (e.g., `0.0.0.0` to listen on all available interfaces).
-   `<listen_port>`: The port on which the receiver should listen.
-   `--key_path`: Path to the encryption key file (must be the same key used by the streamer).

## Project Structure

-   `receiver.py`: The script responsible for receiving, decrypting, decompressing, and displaying the video stream.
-   `setup.py`: Package installation and dependency management.
-   `streamer/`:
    -   `camera.py`: Handles video capture from the camera.
    -   `compression.py`: Manages JPEG compression and decompression.
    -   `main.py`: The core logic for streaming (capture, compress, encrypt, send).
    -   `network.py`: Implements UDP sending and receiving, including packet fragmentation and reassembly.
    -   `security.py`: Provides encryption and decryption functionalities using Fernet.

## Dependencies

The project relies on the following Python libraries, managed via `setup.py`:

-   `opencv-python`: For camera access and image processing.
-   `numpy`: A fundamental package for scientific computing with Python, used by OpenCV.
-   `cryptography`: Provides strong cryptographic primitives for secure communication.

## Contributing

Contributions are welcome! Please feel free to open issues or submit pull requests.

## License

This project is licensed under the MIT License.
