from typing import Callable, Protocol
from logging import getLogger

from math import ceil
from time import sleep
from serial import Serial

from .frame import FoconFrame

LOG = getLogger(__name__)


class FoconTransport(Protocol):
	def read(self) -> bytes:
		...

	def write(self, data: bytes) -> None:
		...

class FoconSerialTransport(FoconTransport):
	BAUDRATE = 57600

	def __init__(self, device: str, sleep_after_tx: float | None = 0.0002, flow_control: bool = True, debug=False) -> None:
		self.serial = Serial(device, baudrate=self.BAUDRATE, rtscts=flow_control)
		self.sleep_after_tx = sleep_after_tx
		self.serial.reset_output_buffer()
		self.serial.reset_input_buffer()
		self.debug = debug

	def read(self) -> bytes:
		self.serial.setRTS(0)
		data: bytes = self.serial.read()
		if self.debug:
			LOG.debug('  <: %s', data.hex())
		return data

	def write(self, data: bytes) -> None:
		if self.debug:
			LOG.debug('  >: %s', data.hex())
		self.serial.setRTS(1)
		self.serial.write(data)
		self.serial.flush()
		if self.sleep_after_tx:
			sleep(self.sleep_after_tx * len(data))
		self.serial.setRTS(0)

class FoconPeer:
	def __init__(self):
		self.frames = []
		self.seq = None
		self.rx = False


class FoconBus:
	def __init__(self, transport: FoconTransport, src_id: int, debug: bool = False) -> None:
		self.transport = transport
		self.src_id = src_id
		self.pending_data = b''
		self.peers: dict[int, FoconPeer] = {}
		self.debug = debug

	def send_message(self, dest_id: int | None, data: bytes) -> None:
		max_frame_size = 512
		nframes = ceil(len(data) / max_frame_size)
		for i in range(nframes):
			frame = FoconFrame(src_id=self.src_id, dest_id=dest_id, num=i + 1, total=nframes, data=data[i * max_frame_size:(i + 1) * max_frame_size])
			if self.debug:
				LOG.debug(' > frame: %s', frame)
			self.send_frame(frame)
			if (i + 1) < nframes:
				assert dest_id is not None
				self.recv_ack(dest_id)

	def send_req(self, dest_id: int) -> None:
		frame = FoconFrame(src_id=self.src_id, dest_id=dest_id, num=0, total=0, data=b'')
		if self.debug:
			LOG.debug(' > req: %r', dest_id)
		return self.send_frame(frame)

	def send_frame(self, frame: FoconFrame) -> None:
		self.transport.write(frame.pack())
		if frame.dest_id not in self.peers:
			self.peers[frame.dest_id] = FoconPeer()
		self.peers[frame.dest_id].rx = True
		self.peers[frame.dest_id].seq = frame.num

	def recv_message(self, peer_id, checker: Callable[[bytes | None], bool] | None = None) -> bytes | None:
		if peer_id not in self.peers:
			self.peers[peer_id] = FoconPeer()

		while True:
			found = False
			for id, peer in self.peers.items():
				if not peer.frames:
					continue
				if peer.frames[-1].is_nak:
					frame_data = None
				elif peer.frames[-1].num == peer.seq:
					frame_data = b''.join(f.data for f in sorted(peer.frames, key=lambda f: f.num)) or None
				else:
					continue
				if not checker or checker(frame_data):
					found = True
					break

			if found:
				peer.frames = []
				peer.seq = None
				return frame_data

			frame = None
			while not frame:
				if not self.peers[peer_id].rx:
					self.send_req(peer_id)
				frame = self.recv_frame()

			if frame.src_id not in self.peers:
				self.peers[frame.src_id] = FoconPeer()
			self.peers[frame.src_id].rx = False
			self.peers[frame.src_id].frames.append(frame)

	def recv_frame(self) -> FoconFrame | None:
		while True:
			self.pending_data += self.transport.read()
			try:
				frame, self.pending_data = FoconFrame.unpack(self.pending_data)
				if frame.dest_id not in (self.src_id, None):
					continue
				if self.debug:
					LOG.debug(' < frame: %r', frame)
				return frame
			except EOFError:
				return None
			except:
				LOG.warn('Error parsing frame data %s, discarding', self.pending_data.hex())
				self.pending_data = b''
				return None

	def recv_ack(self, dest_id: int) -> None:
		self.recv_message(dest_id, lambda data: data is None)

	def recv_next_message(self, dest_id: int, checker: Callable[[bytes | None], bool] | None) -> bytes | None:
		def inner_checker(data: bytes | None) -> bool:
			if data is None:
				return True
			return not checker or checker(data)
		data = self.recv_message(dest_id, inner_checker)
		if not data:
			return None
		return data
