from typing import Callable, Any

from struct import unpack
from dataclasses import dataclass
from enum import Enum

from ..message import FoconMessageBus


def decode_version(data: bytes) -> tuple[int, int]:
	return int(data[0:1].decode('ascii'), 10), int(data[1:3].decode('ascii'), 10)

def encode_version(ver: tuple[int, int]) -> bytes:
	major = str(ver[0]).encode('ascii')
	minor = str(ver[1]).encode('ascii')
	return major + minor

class FoconDeviceCommand(Enum):
	BootInfo          = 0x0041

class FoconBootMode(Enum):
	BootLoader = 'B'
	Application = 'A'

@dataclass
class FoconDeviceInfo:
	kind: str
	mode: FoconBootMode
	boot_version: tuple[int, int]
	app_version: tuple[int, int] | None

	def pack(self) -> bytes:
		b = b''

		# 0x00..0x02
		b += bytes([
			ord(self.kind),
			ord(self.mode.value)]
		)
		# 0x02..0x05
		b += encode_version(self.boot_version)
		# 0x05..0x08
		b += encode_version(self.app_version) if self.app_version else b'???'

		return b

	@classmethod
	def unpack(cls, data: bytes) -> 'FoconDeviceInfo':
		return cls(
			kind=chr(data[0]),
			mode=FoconBootMode(chr(data[1])),
			boot_version=decode_version(data[2:5]),
			app_version=decode_version(data[5:8]) if data[5:8] != b'???' else None,
		)

	def __repr__(self) -> str:
		s = f'{self.__class__.__name__} {{ {self.kind}, {self.mode.name.lower()}, boot: {self.boot_version[0]}.{self.boot_version[1]:02}'
		if self.app_version:
			s += f', app: {self.app_version[0]}.{self.app_version[1]:02}'
		s += ' }'
		return s


def encode_str(s: str, size: int) -> bytes:
	sb = s.encode('iso-8859-15')
	if len(sb) > size:
		raise ValueError('over-sized string: {} can not fit in {} bytes'.format(s, size))
	return sb.ljust(size, b'\0')

def decode_str(data: bytes) -> str:
	if b'\0' in data:
		data = data[:data.index(b'\0')]
	return data.decode('iso-8859-15')

def dangerous(fn: Callable[..., Any]) -> Callable[..., Any]:
	return fn


class FoconDevice:
	def __init__(self, bus: FoconMessageBus, dest_id: int) -> None:
		self.bus = bus
		self.dest_id = dest_id

	def send_command(self, command: int, payload: bytes = b'') -> bytes:
		return self.bus.send_command(self.dest_id, command, payload=payload)

	def recv_message(self, cmd: int | None = None) -> bytes:
		return self.bus.recv_message(self.dest_id, cmd=cmd)

	def recv_messages(self, cmd: int | None = None) -> bytes:
		return self.bus.recv_messages(self.dest_id, cmd=cmd)


	def send_device_command(self, command: FoconDeviceCommand, payload: bytes = b'') -> bytes:
		return self.send_command(command.value, payload=payload)

	def get_device_info(self) -> FoconDeviceInfo:
		response = self.send_device_command(FoconDeviceCommand.BootInfo)
		return FoconDeviceInfo.unpack(response)
