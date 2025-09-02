import argparse
import time
import logging_mp as logging
from streamer.camera import Camera
from streamer.compression import Compressor
from streamer.network import UDPSender
from streamer.security import Encryptor

# Configure logging for better diagnostics
logging.basic_config(level=logging.INFO)
logger = logging.get_logger(__name__)

def main():
    """
    Main function to capture, compress, encrypt, and stream video frames.
    """
    parser = argparse.ArgumentParser(description="Secure Camera Streamer")
    parser.add_argument("host", type=str, help="The IP address of the receiving host.")
    parser.add_argument("port", type=int, help="The port number of the receiving host.")
    parser.add_argument(
        "--camera_index",
        type=int,
        default=0,
        help="The index of the camera to use (default: 0)."
    )
    parser.add_argument(
        "--key_path",
        type=str,
        default="secret.key",
        help="Path to the encryption key file (default: secret.key)."
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=90,
        choices=range(1, 101),
        metavar="[1-100]",
        help="JPEG compression quality (default: 90)."
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["unicast", "multicast"],
        default="unicast",
        help="Streaming mode: 'unicast' (default) or 'multicast'"
    )
    parser.add_argument(
        "--mcast_addr",
        type=str,
        default="239.1.2.3",
        help="Multicast group address (used in multicast mode)"
    )
    parser.add_argument(
        "--interface",
        type=str,
        default=None,
        help="Network interface IP to use for multicast (optional)"
    )
    parser.add_argument(
        "--loopback",
        action="store_true",
        help="Enable multicast loopback (sender receives its own packets)"
    )
    parser.add_argument(
        "--ttl",
        type=int,
        default=1,
        help="Multicast TTL (default: 1, local subnet only)"
    )
    args = parser.parse_args()

    # --- Initialization of Modules ---
    try:
        logger.info("Initializing components...")
        camera = Camera(camera_index=args.camera_index)
        compressor = Compressor(quality=args.quality)
        encryptor = Encryptor.from_file(args.key_path)
        if args.mode == "multicast":
            from streamer.network import get_sender
            sender = get_sender(
                mode="multicast",
                mcast_addr=args.mcast_addr,
                port=args.port,
                interface=args.interface,
                loopback=args.loopback,
                ttl=args.ttl
            )
            logger.info(f"Multicast mode: streaming to {args.mcast_addr}:{args.port} (interface: {args.interface or 'default'})")
        else:
            from streamer.network import get_sender
            sender = get_sender(
                mode="unicast",
                host=args.host,
                port=args.port
            )
            logger.info(f"Unicast mode: streaming to {args.host}:{args.port}")
        logger.info(f"Components initialized. Streaming to {args.host}:{args.port}")
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        return

    # --- Main Streaming Loop ---
    try:
        frame_count = 0
        start_time = time.time()
        while True:
            # 1. Capture
            send_time_ns = time.time_ns()
            frame = camera.capture_frame()

            if frame is None:
                logger.warning("Failed to capture frame, skipping.")
                time.sleep(0.1) # Wait a bit before retrying
                continue

            # 2. Compress
            compressed_frame = compressor.compress(frame)

            # 3. Encrypt
            encrypted_frame = encryptor.encrypt(compressed_frame)
            
            # 4. Send
            sender.send(encrypted_frame, send_time_ns)

            frame_count += 1
            if time.time() - start_time >= 1.0:
                throughput = frame_count / (time.time() - start_time)
                logger.info(f"Throughput: {throughput:.2f} frames/sec")
                frame_count = 0
                start_time = time.time()

    except KeyboardInterrupt:
        logger.info("Streaming stopped by user.")
    except Exception as e:
        logger.error(f"An unexpected error occurred during streaming: {e}")
    finally:
        # --- Cleanup ---
        logger.info("Closing resources.")
        camera.release()
        sender.close()
        logger.info("Streamer shut down.")

if __name__ == "__main__":
    main()

