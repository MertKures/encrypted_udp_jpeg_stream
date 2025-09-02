import socket
import logging_mp as logging
from typing import Tuple
import time
import struct

logger = logging.get_logger(__name__)

MAX_UDP_PAYLOAD_SIZE = 32  # Maximum UDP payload size is 1472 (1500 bytes MTU - 20 bytes IP header - 8 bytes UDP header).

class UDPSender:
    """
    Handles sending data over UDP.
    
    UDP is used because it's a "fire-and-forget" protocol. It has very low
    overhead, which maximizes throughput. It doesn't guarantee packet delivery
    or order, which is acceptable for a real-time video stream where receiving
    the latest frame quickly is more important than receiving every single frame.
    """
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_address = (self.host, self.port)

    def _create_packet(self, frame_id: int, sequence_num: int, is_last_packet: bool, send_time_ns: int, payload: bytes) -> bytes:
        header = f"{frame_id}:{sequence_num}:{int(is_last_packet)}:{send_time_ns}:".encode('utf-8')
        return header + payload

    def send(self, data: bytes, send_time_ns: int):
        """Sends a bytes payload to the target host, splitting into smaller packets if necessary."""
        frame_id = time.time_ns() # Unique ID for each frame
        sequence_num = 0
        for i in range(0, len(data), MAX_UDP_PAYLOAD_SIZE):
            chunk = data[i:i + MAX_UDP_PAYLOAD_SIZE]
            is_last_packet = (i + MAX_UDP_PAYLOAD_SIZE) >= len(data)
            packet = self._create_packet(frame_id, sequence_num, is_last_packet, send_time_ns, chunk)
            try:
                self.sock.sendto(packet, self.server_address)
                sequence_num += 1
            except socket.error as e:
                logger.error(f"Socket error while sending data: {e}")
                break # Stop sending further packets if an error occurs

    def close(self):
        """Closes the socket."""
        self.sock.close()

class UDPReceiver:
    """Handles receiving data over UDP."""
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        logger.info(f"UDP Receiver listening on {self.host}:{self.port}")
        self.incomplete_frames = {}
        self.last_received_time_ns = None
        self.inter_arrival_times = []
        self.jitter_log_interval = 100 # Log jitter every 100 packets

    def receive(self, buffer_size: int = 65535) -> bytes:
        """
        Receives a single UDP packet.
        
        Args:
            buffer_size (int): The maximum number of bytes to receive. Should be
                               large enough for any expected packet.
        
        Returns:
            The received data as bytes.
        """
        try:
            data, _ = self.sock.recvfrom(buffer_size)
            return data
        except socket.error as e:
            logger.error(f"Socket error while receiving data: {e}")
            return b''

    def receive_frame(self, buffer_size: int = 65535) -> Tuple[bytes, int]:
        while True:
            packet_data = self.receive(buffer_size)
            if not packet_data:
                continue

            try:
                # Parse header: "frame_id:sequence_num:is_last_packet:send_time_ns:"
                first_colon_idx = packet_data.find(b':')
                second_colon_idx = packet_data.find(b':', first_colon_idx + 1)
                third_colon_idx = packet_data.find(b':', second_colon_idx + 1)
                header_end_idx = packet_data.find(b':', third_colon_idx + 1)

                if header_end_idx == -1:
                    logger.warning("Malformed packet header received, skipping.")
                    continue
                
                header_parts = packet_data[:header_end_idx].decode('utf-8').split(':')
                
                frame_id = int(header_parts[0])
                sequence_num = int(header_parts[1])
                is_last_packet = bool(int(header_parts[2]))
                send_time_ns = int(header_parts[3])
                payload = packet_data[header_end_idx + 1:]

                current_receive_time_ns = time.time_ns()
                if self.last_received_time_ns is not None:
                    inter_arrival_time = current_receive_time_ns - self.last_received_time_ns
                    self.inter_arrival_times.append(inter_arrival_time)
                    
                    if len(self.inter_arrival_times) >= self.jitter_log_interval:
                        avg_inter_arrival_time = (sum(self.inter_arrival_times) / len(self.inter_arrival_times)) / 1e6
                        # Jitter can be calculated as the mean deviation of inter-arrival times
                        jitter = (sum(abs(t - avg_inter_arrival_time) for t in self.inter_arrival_times) / len(self.inter_arrival_times)) / 1e6
                        logger.info(f"Jitter (ms): {jitter:.2f}, Avg Inter-arrival Time (ms): {avg_inter_arrival_time:.2f}")
                        self.inter_arrival_times = [] # Reset for next interval
                self.last_received_time_ns = current_receive_time_ns

                if frame_id not in self.incomplete_frames:
                    self.incomplete_frames[frame_id] = {"send_time_ns": send_time_ns, "packets": {}}
                
                self.incomplete_frames[frame_id]["packets"][sequence_num] = payload

                if is_last_packet:
                    # Reassemble the frame
                    sorted_packets = sorted(self.incomplete_frames[frame_id]["packets"].items())
                    full_frame_data = b"".join([payload for _, payload in sorted_packets])
                    
                    frame_info = self.incomplete_frames[frame_id]
                    del self.incomplete_frames[frame_id] # Clean up
                    return full_frame_data, frame_info["send_time_ns"]

            except (ValueError, IndexError) as e:
                logger.error(f"Error parsing packet: {e}")
            except Exception as e:
                logger.error(f"Unexpected error in receive_frame: {e}")

    def close(self):
        """Closes the socket."""
        self.sock.close()

class MulticastSender:
    """
    Handles sending data over UDP multicast.
    """
    def __init__(self, mcast_addr: str, port: int, interface: str = None, loopback: bool = False, ttl: int = 1):
        self.mcast_addr = mcast_addr
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        # Set TTL
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        # Set loopback
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, int(loopback))
        # Set outgoing interface if specified
        if interface:
            self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(interface))
        self.server_address = (self.mcast_addr, self.port)

    def _create_packet(self, frame_id: int, sequence_num: int, is_last_packet: bool, send_time_ns: int, payload: bytes) -> bytes:
        header = f"{frame_id}:{sequence_num}:{int(is_last_packet)}:{send_time_ns}:".encode('utf-8')
        return header + payload

    def send(self, data: bytes, send_time_ns: int):
        frame_id = time.time_ns()
        sequence_num = 0
        for i in range(0, len(data), MAX_UDP_PAYLOAD_SIZE):
            chunk = data[i:i + MAX_UDP_PAYLOAD_SIZE]
            is_last_packet = (i + MAX_UDP_PAYLOAD_SIZE) >= len(data)
            packet = self._create_packet(frame_id, sequence_num, is_last_packet, send_time_ns, chunk)
            try:
                self.sock.sendto(packet, self.server_address)
                sequence_num += 1
            except socket.error as e:
                logger.error(f"Socket error while sending multicast data: {e}")
                break

    def close(self):
        self.sock.close()

class MulticastReceiver:
    """
    Handles receiving data over UDP multicast.
    """
    def __init__(self, mcast_addr: str, port: int, interface: str = None):
        self.mcast_addr = mcast_addr
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        # Allow multiple sockets to use the same PORT number
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Always bind to all interfaces for multicast
        self.sock.bind(('', self.port))
        # Join multicast group on the specified interface
        if interface:
            mreq = struct.pack('4s4s', socket.inet_aton(self.mcast_addr), socket.inet_aton(interface))
        else:
            mreq = struct.pack('4s4s', socket.inet_aton(self.mcast_addr), socket.inet_aton('0.0.0.0'))
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        logger.info(f"Multicast Receiver listening on {self.mcast_addr}:{self.port} (interface: {interface or 'default'})")
        self.incomplete_frames = {}
        self.last_received_time_ns = None
        self.inter_arrival_times = []
        self.jitter_log_interval = 100

    def receive(self, buffer_size: int = 65535) -> bytes:
        try:
            data, _ = self.sock.recvfrom(buffer_size)
            return data
        except socket.error as e:
            logger.error(f"Socket error while receiving multicast data: {e}")
            return b''

    def receive_frame(self, buffer_size: int = 65535) -> Tuple[bytes, int]:
        while True:
            packet_data = self.receive(buffer_size)
            if not packet_data:
                continue
            try:
                first_colon_idx = packet_data.find(b':')
                second_colon_idx = packet_data.find(b':', first_colon_idx + 1)
                third_colon_idx = packet_data.find(b':', second_colon_idx + 1)
                header_end_idx = packet_data.find(b':', third_colon_idx + 1)
                if header_end_idx == -1:
                    logger.warning("Malformed packet header received, skipping.")
                    continue
                header_parts = packet_data[:header_end_idx].decode('utf-8').split(':')
                frame_id = int(header_parts[0])
                sequence_num = int(header_parts[1])
                is_last_packet = bool(int(header_parts[2]))
                send_time_ns = int(header_parts[3])
                payload = packet_data[header_end_idx + 1:]
                current_receive_time_ns = time.time_ns()
                if self.last_received_time_ns is not None:
                    inter_arrival_time = current_receive_time_ns - self.last_received_time_ns
                    self.inter_arrival_times.append(inter_arrival_time)
                    if len(self.inter_arrival_times) >= self.jitter_log_interval:
                        avg_inter_arrival_time = (sum(self.inter_arrival_times) / len(self.inter_arrival_times)) / 1e6
                        jitter = (sum(abs(t - avg_inter_arrival_time) for t in self.inter_arrival_times) / len(self.inter_arrival_times)) / 1e6
                        logger.info(f"Jitter (ms): {jitter:.2f}, Avg Inter-arrival Time (ms): {avg_inter_arrival_time:.2f}")
                        self.inter_arrival_times = []
                self.last_received_time_ns = current_receive_time_ns
                if frame_id not in self.incomplete_frames:
                    self.incomplete_frames[frame_id] = {"send_time_ns": send_time_ns, "packets": {}}
                self.incomplete_frames[frame_id]["packets"][sequence_num] = payload
                if is_last_packet:
                    sorted_packets = sorted(self.incomplete_frames[frame_id]["packets"].items())
                    full_frame_data = b"".join([payload for _, payload in sorted_packets])
                    frame_info = self.incomplete_frames[frame_id]
                    del self.incomplete_frames[frame_id]
                    return full_frame_data, frame_info["send_time_ns"]
            except (ValueError, IndexError) as e:
                logger.error(f"Error parsing multicast packet: {e}")
            except Exception as e:
                logger.error(f"Unexpected error in multicast receive_frame: {e}")

    def close(self):
        self.sock.close()

def get_sender(mode: str, **kwargs):
    if mode == 'multicast':
        return MulticastSender(
            mcast_addr=kwargs['mcast_addr'],
            port=kwargs['port'],
            interface=kwargs.get('interface'),
            loopback=kwargs.get('loopback', False),
            ttl=kwargs.get('ttl', 1)
        )
    else:
        return UDPSender(host=kwargs['host'], port=kwargs['port'])

def get_receiver(mode: str, **kwargs):
    if mode == 'multicast':
        return MulticastReceiver(
            mcast_addr=kwargs['mcast_addr'],
            port=kwargs['port'],
            interface=kwargs.get('interface')
        )
    else:
        return UDPReceiver(host=kwargs['host'], port=kwargs['port'])


