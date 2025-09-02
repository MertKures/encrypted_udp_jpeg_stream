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

1.**Clone the repository:**

```bash
git clone https://github.com/MertKures/encrypted_udp_jpeg_stream.git
cd encrypted_udp_jpeg_stream
```

2.**Install uv if you haven't yet**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## How to use it ?

First, create a secret key and share it with the receiver.

### Creating a secret key

```bash
uv run streamer/security.py
```

Then, select your communication type:

- Unicast
- Multicast

**Note: 192.168.1.100 and 192.168.1.115 ip addresses will be used as receiver and sender respectively throughout this README.md for demonstration purposes.**

### Unicast

#### Starting the unicast sender

```bash
uv run __main__.py 192.168.1.100 5555 --quality 90
```

#### Starting the unicast receiver

```bash
uv run receiver.py 192.168.1.100 5555
```

---

### Multicast

#### Starting the multicast sender

- **--loopback:** This should be added to the arguments if working on the same machine. By default, we are assuming that sender and receiver is on the same machine.
- **--interface:** If not working on localhost, this should have the ip address of the network interface you want to use. This could be 192.168.1.115 for example.

```bash
uv run __main__.py 239.1.2.3 5555 --mode multicast --quality 90 --loopback
```

or

```bash
uv run __main__.py 239.1.2.3 5555 --mode multicast --quality 90 --interface 192.168.1.115
```

#### Starting the multicast receiver

```bash
uv run receiver.py 239.1.2.3 5555 --mode multicast
```

or

```bash
uv run receiver.py 239.1.2.3 5555 --mode multicast --interface 192.168.1.100
```

## Project Structure

- `receiver.py`: The script responsible for receiving, decrypting, decompressing, and displaying the video stream.
- `setup.py`: Package installation and dependency management.
- `__main__.py`: The core logic for streaming (capture, compress, encrypt, send).
- `streamer/`:
  - `camera.py`: Handles video capture from the camera.
  - `compression.py`: Manages JPEG compression and decompression.
  - `network.py`: Implements UDP sending and receiving, including packet fragmentation and reassembly.
  - `security.py`: Provides encryption and decryption functionalities using Fernet.

## Dependencies

The project relies on the following Python libraries, managed via uv:

- `opencv-python`
- `numpy`
- `cryptography`
- `logging-mp`

## Contributing

Contributions are welcome! Please feel free to open issues or submit pull requests.

## License

This project is licensed under the MIT License.

## FAQs

### I don't get images when sender and receiver have the same ip address

- You should use **--loopback** argument if sender and receiver are on the same machine. Let's assume your ip address is 192.168.115 for both sender and receiver. You need to pass **--loopback** to the sender to be able to receive images from the receiver.

### Frames get corrupted a lot / delay is too high

- Try adjusting the **--quality** option and the `MAX_UDP_PAYLOAD_SIZE` variable in `streamer/network.py`. For Wi-Fi connections, lower the payload size (e.g., 32); for wired connections, you can use higher values, up to a maximum of 1472.
