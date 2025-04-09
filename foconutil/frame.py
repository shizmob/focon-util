from typing import ClassVar
from logging import getLogger

from struct import pack
from dataclasses import dataclass
import crcmod

from .util import take, take_unpack

LOG = getLogger(__name__)

CRC = crcmod.mkCrcFun(0x18005, 0xffff, False)

@dataclass
class FoconFrame:
	PREAMBLE = b'\xFF\xFF\xFF\x01'
	POSTAMBLE = b'\xFF'
	ID_MAP: ClassVar[dict[int | None, bytes]] = {i: bytes([x]) for i, x in enumerate(b'IJKLMNOpqrstuvwx')}
	ID_MAP[None] = b'*'
	REVERSE_ID_MAP = {v: k for k, v in ID_MAP.items()}

	src_id:  int
	dest_id: int | None
	num:     int
	total:   int
	data:    bytes

	def pack(self) -> bytes:
		if self.src_id not in self.ID_MAP:
			raise ValueError(f'invalid source ID: {self.src_id}')
		src = self.ID_MAP[self.src_id]
		if self.dest_id not in self.ID_MAP:
			raise ValueError(f'invalid destination ID: {self.dest_id}')
		dest = self.ID_MAP[self.dest_id]

		cdata = pack('>ccBB', src, dest, self.total, self.num)
		cdata += pack('>H', len(self.data)) + self.data

		checksum = CRC(cdata)
		data = self.PREAMBLE + cdata + pack('>H', checksum) + self.POSTAMBLE
		return data

	@classmethod
	def unpack(cls, data: bytes) -> tuple['FoconFrame', bytes]:
		odata = data

		while data and data[0] == 0xff:
			data = data[1:]
		if not data:
			raise EOFError()
		if data[0] != 1:
			raise ValueError(f'invalid preamble: {odata!r}')
		data = data[1:]
		cdata = data

		(src, dest, total, num, pdata_length), data = take_unpack(data, '>ccBBH')
		if src not in cls.REVERSE_ID_MAP:
			raise ValueError(f'invalid source: {src}')
		src_id = cls.REVERSE_ID_MAP[src]
		if dest not in cls.REVERSE_ID_MAP:
			raise ValueError(f'invalid destination: {dest}')
		dest_id = cls.REVERSE_ID_MAP[dest]

		pdata, data = take(data, pdata_length)
		cdata = cdata[:-len(data)]
		expected_checksum = CRC(cdata)

		(checksum,), data = take_unpack(data, '>H')
		if checksum != expected_checksum:
			raise ValueError(f'incorrect checksum: {checksum} != {expected_checksum}')

		postamble, data = take(data, len(cls.POSTAMBLE))
		if postamble != cls.POSTAMBLE:
			raise ValueError(f'invalid postamble: {postamble!r}')

		assert src_id is not None
		return cls(src_id=src_id, dest_id=dest_id, num=num, total=total, data=pdata), data

	@property
	def is_ack(self):
		return not self.data and self.total > 0

	@property
	def is_nak(self):
		return not self.data and self.total == 0

	def __repr__(self) -> str:
		s = f'{self.__class__.__name__} #{self.num}/#{self.total} {{ {self.src_id} -> {self.dest_id}'
		if self.data:
			s += f', data: {self.data.hex()}'
		s += ' }'
		return s
