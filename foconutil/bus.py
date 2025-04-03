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

class FoconBus:
	def __init__(self, transport: FoconTransport, src_id: int, debug: bool = False) -> None:
		self.transport = transport
		self.src_id = src_id
		self.pending_data = b''
		self.pending_frames: dict[int, list[FoconFrame]] = {}
		self.debug = debug

	def send_message(self, dest_id: int | None, data: bytes) -> None:
		max_frame_size = 512
		nframes = ceil(len(data) / max_frame_size)
		for i in range(nframes):
			frame = FoconFrame(src_id=self.src_id, dest_id=dest_id, num=i + 1, total=nframes, data=data[i * max_frame_size:(i + 1) * max_frame_size])
			self.send_frame(frame)
			if (i + 1) < nframes:
				assert dest_id is not None
				self.recv_ack(dest_id)

	def send_frame(self, frame: FoconFrame) -> None:
		if self.debug:
			LOG.debug(' > frame: %r', frame)
		self.transport.write(frame.pack())

	def send_ack(self, dest_id: int) -> None:
		frame = FoconFrame(src_id=self.src_id, dest_id=dest_id, num=0, total=0, data=b'')
		if self.debug:
			LOG.debug(' > ack: %r', dest_id)
		self.transport.write(frame.pack())

	def recv_message(self, checker: Callable[[bytes | None], bool] | None = None) -> bytes | None:
		while True:
			found = False
			for src_id, frames in self.pending_frames.items():
				if not frames or not frames[-1]:
					continue
				if frames[-1].total not in (0, len(frames)):
					continue
				if frames[-1].total == 0:
					frame_data = None
				else:
					frame_data = b''.join(f.data for f in sorted([f for f in frames if f], key=lambda f: f.num))
				if not checker or checker(frame_data):
					found = True
					break

			if found:
				del self.pending_frames[src_id]
				return frame_data

			frame = None
			while not frame:
				frame = self.recv_frame()
			if frame.dest_id not in (self.src_id, None):
				continue
			self.pending_frames.setdefault(frame.src_id, []).append(frame)
			if frame.num < frame.total:
				self.send_ack(frame.src_id)

	def recv_frame(self) -> FoconFrame | None:
		self.pending_data += self.transport.read()
		try:
			frame, self.pending_data = FoconFrame.unpack(self.pending_data)
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
		self.recv_message(lambda data: data is None)
		self.pending_frames.setdefault(dest_id, []).append(None)

	def recv_next_message(self, dest_id: int, checker: Callable[[bytes | None], bool] | None) -> bytes | None:
		self.send_ack(dest_id)

		def inner_checker(data: bytes | None) -> bool:
			if data is None:
				return True
			return not checker or checker(data)
		data = self.recv_message(inner_checker)
		if not data:
			return None
		return data
