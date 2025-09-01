import argparse
import logging
import cv2
import time
from streamer.network import UDPReceiver
from streamer.security import Encryptor
from streamer.compression import Compressor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """
    Main function to receive, decrypt, decompress, and display video frames.
    """
    parser = argparse.ArgumentParser(description="Secure Camera Stream Receiver")
    parser.add_argument("port", type=int, help="The port number to listen on.")
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="The IP address to bind to (default: 0.0.0.0, listens on all interfaces)."
    )
    parser.add_argument(
        "--key_path",
        type=str,
        default="secret.key",
        help="Path to the encryption key file (default: secret.key)."
    )
    args = parser.parse_args()

    # --- Initialization ---
    try:
        logging.info("Initializing receiver components...")
        receiver = UDPReceiver(host=args.host, port=args.port)
        encryptor = Encryptor.from_file(args.key_path)
        compressor = Compressor()
        logging.info("Receiver initialized. Waiting for stream...")
    except Exception as e:
        logging.error(f"Failed to initialize components: {e}")
        return

    # --- Main Receiving Loop ---
    window_name = "Secure Stream"
    frame_count = 0
    start_time = time.time()
    try:
        while True:
            # 1. Receive
            encrypted_packet, send_time_ns = receiver.receive_frame()
            if not encrypted_packet:
                continue

            # Calculate delay
            receive_time_ns = time.time_ns()
            delay_ms = (receive_time_ns - send_time_ns) / 1_000_000.0
            logging.info(f"Packet Delay: {delay_ms:.2f} ms")

            # 2. Decrypt
            compressed_frame = encryptor.decrypt(encrypted_packet)
            if compressed_frame is None:
                logging.warning(f'The frame is probably corrupted.')
                # The packet was invalid/corrupted and has been dropped.
                continue

            # 3. Decompress
            frame = compressor.decompress(compressed_frame)

            # 4. Display
            cv2.imshow(window_name, frame)
            
            frame_count += 1
            if time.time() - start_time >= 1.0:
                throughput = frame_count / (time.time() - start_time)
                logging.info(f"Receiver Throughput: {throughput:.2f} frames/sec")
                frame_count = 0
                start_time = time.time()

            # Exit on 'q' key press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        logging.info("Receiver stopped by user.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    finally:
        # --- Cleanup ---
        logging.info("Closing resources.")
        receiver.close()
        cv2.destroyAllWindows()
        logging.info("Receiver shut down.")

if __name__ == "__main__":
    main()
