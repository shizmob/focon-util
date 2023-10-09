from typing import Callable
from logging import getLogger

from time import sleep
from serial import Serial

from .frame import FoconFrame

LOG = getLogger(__name__)


class FoconBus:
	BAUDRATE = 57600

	def __init__(self, device: str, src_id: int, sleep_after_tx: float | None = 0.0002) -> None:
		self.serial = Serial(device, baudrate=self.BAUDRATE, rtscts=True)
		self.src_id = src_id
		self.pending_data = b''
		self.pending_frames: dict[int, list[FoconFrame]] = {}
		self.serial.reset_output_buffer()
		self.serial.reset_input_buffer()
		self.sleep_after_tx = sleep_after_tx

	def send_data(self, data: bytes) -> None:
		LOG.debug('>>: %s', data.hex())
		self.serial.setRTS(1)
		self.serial.write(data)
		self.serial.flush()
		if self.sleep_after_tx:
			sleep(self.sleep_after_tx * len(data))
		self.serial.setRTS(0)

	def recv_data(self) -> bytes:
		self.serial.setRTS(0)
		data: bytes = self.serial.read()
		LOG.debug('<<: %s', data.hex())
		return data

	def send_frame(self, dest_id: int | None, data: bytes) -> None:
		frame = FoconFrame(src_id=self.src_id, dest_id=dest_id, num=1, total=1, data=data)
		LOG.debug('>> frame: %r', frame)
		self.send_data(frame.pack())

	def send_ack(self, dest_id: int) -> None:
		frame = FoconFrame(src_id=self.src_id, dest_id=dest_id, num=0, total=0, data=b'')
		LOG.debug('>> ack: %r', dest_id)
		self.send_data(frame.pack())

	def recv_frame(self, checker: Callable[[bytes | None], bool] | None = None) -> bytes | None:
		while True:
			found = False
			for src_id, frames in self.pending_frames.items():
				if not frames:
					continue
				if frames[-1].total not in (0, len(frames)):
					continue
				if frames[-1].total == 0:
					frame_data = None
				else:
					frame_data = b''.join(f.data for f in sorted(frames, key=lambda f: f.num))
				if not checker or checker(frame_data):
					found = True
					break

			if found:
				del self.pending_frames[src_id]
				return frame_data

			self.pending_data += self.recv_data()
			try:
				frame, self.pending_data = FoconFrame.unpack(self.pending_data)
				LOG.debug('<< frame: %r', frame)
			except EOFError:
				continue
			except:
				LOG.warn('Error parsing frame data %s, discarding', self.pending_data.hex())
				self.pending_data = b''
				continue

			if frame.dest_id not in (self.src_id, None):
				continue
			self.pending_frames.setdefault(frame.src_id, []).append(frame)
			if frame.num < frame.total:
				self.send_ack(frame.src_id)

	def recv_next_frame(self, dest_id: int | None, checker: Callable[[bytes | None], bool] | None) -> bytes | None:
		frame = FoconFrame(src_id=self.src_id, dest_id=dest_id, num=0, total=0, data=b'')
		LOG.debug('>> frame: %r', frame)
		self.send_data(frame.pack())

		def inner_checker(data: bytes | None) -> bool:
			if data is None:
				return True
			return not checker or checker(data)
		data = self.recv_frame(inner_checker)
		if not data:
			return None
		return data
