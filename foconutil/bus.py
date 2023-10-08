from typing import Callable
from logging import getLogger

from time import sleep
from serial import Serial

from .frame import FoconFrame

LOG = getLogger(__name__)


class FoconBus:
	BAUDRATE = 57600

	def __init__(self, device: str, src_id: int | None = None, sleep_after_tx: float | None = 0.005) -> None:
		self.serial = Serial(device, baudrate=self.BAUDRATE, rtscts=True)
		self.src_id = None
		self.pending_data = b''
		self.pending_frames: list[FoconFrame] = []
		self.serial.reset_output_buffer()
		self.serial.reset_input_buffer()
		self.sleep_after_tx = sleep_after_tx

	def send_data(self, data: bytes) -> None:
		LOG.debug('>>: %s', data.hex())
		self.serial.setRTS(1)
		self.serial.write(data)
		self.serial.flush()
		if self.sleep_after_tx:
			sleep(self.sleep_after_tx)
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

	def recv_frame(self, checker: Callable[[FoconFrame], bool] | None = None) -> FoconFrame:
		while True:
			found = False
			for p in self.pending_frames:
				if not checker or checker(p):
					found = True
					break

			if found:
				self.pending_frames.remove(p)
				return p

			self.pending_data += self.recv_data()
			try:
				frame, self.pending_data = FoconFrame.unpack(self.pending_data)
				LOG.debug('<< frame: %r', frame)
			except EOFError:
				continue
			if frame.dest_id not in (self.src_id, None):
				continue
			self.pending_frames.append(frame)

