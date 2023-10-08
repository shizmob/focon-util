from typing import ClassVar
from logging import getLogger

from dataclasses import dataclass
from struct import pack

from .util import take, take_unpack
from .frame import FoconFrame
from .bus import FoconBus

LOG = getLogger(__name__)


@dataclass
class FoconMessage:
	ID_MAP: ClassVar[dict[int | None, bytes]] = {i: 'I{}'.format(i).encode('ascii') for i in range(16)}
	ID_MAP[None] = b'I*'
	REVERSE_ID_MAP = {v: k for k, v in ID_MAP.items()}

	src_id: int | None
	dest_id: int | None
	cmd: int
	value: bytes

	def pack(self) -> bytes:
		if self.src_id not in self.ID_MAP:
			raise ValueError(f'invalid source ID: {self.src_id}')
		src = self.ID_MAP[self.src_id]
		if self.dest_id not in self.ID_MAP:
			raise ValueError(f'invalid destination ID: {self.dest_id}')
		dest = self.ID_MAP[self.dest_id]

		return pack('>2sH2sHH', src, 0x00, dest, len(self.value), self.cmd) + self.value

	@classmethod
	def unpack(cls, data: bytes) -> tuple['FoconMessage', bytes]:
		(src, unk1, dest, vlength, cmd), data = take_unpack(data, '>2sH2sHH')
		value, data = take(data, vlength)
		if data:
			raise ValueError(f'trailing message data: {data!r}')

		if src not in cls.REVERSE_ID_MAP:
			raise ValueError(f'invalid source: {src}')
		src_id = cls.REVERSE_ID_MAP[src]
		if dest not in cls.REVERSE_ID_MAP:
			raise ValueError(f'invalid destination: {dest}')
		dest_id = cls.REVERSE_ID_MAP[dest]

		return cls(src_id=src_id, dest_id=dest_id, cmd=cmd, value=value), data

	def __repr__(self) -> str:
		s = f'{self.__class__.__name__} {{ {self.src_id} -> {self.dest_id}, cmd {self.cmd}'
		if self.value:
			s += f', data: {self.value.hex()}'
		s += ' }'
		return s

class FoconMessageBus:
	def __init__(self, frame_bus: FoconBus, src_id: int | None = None) -> None:
		self.bus = frame_bus
		self.src_id = 0

	def send_message(self, dest_id: int | None, message: FoconMessage) -> None:
		LOG.debug('>> msg: %r', message)
		return self.bus.send_frame(dest_id, message.pack())

	def recv_message(self, cmd: int | None = None) -> FoconMessage:
		def checker(frame: FoconFrame) -> bool:
			try:
				message, _ = FoconMessage.unpack(frame.data)
			except Exception as e:
				print(f'Could not parse {frame}: {e!r}')
				return False
			return message.dest_id in (self.src_id, None) and cmd in (None, message.cmd)

		frame = self.bus.recv_frame(checker)
		msg, remainder_data = FoconMessage.unpack(frame.data)
		LOG.debug('<< msg: %r', msg)
		if remainder_data:
			raise ValueError(f'Remainder data: {remainder_data!r}')
		return msg

	def send_command(self, dest_id: int | None, command: int, payload: bytes=b'') -> bytes:
		message = FoconMessage(src_id=self.src_id, dest_id=dest_id, cmd=command, value=payload)
		self.send_message(dest_id, message)
		reply_message = self.recv_message(cmd=command)
		return reply_message.value
