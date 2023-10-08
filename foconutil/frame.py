from typing import ClassVar
from logging import getLogger

from struct import pack
from dataclasses import dataclass
import crc

from .util import take, take_unpack

LOG = getLogger(__name__)


@dataclass
class FoconFrame:
	PREAMBLE = b'\xFF\xFF\xFF\x01'
	POSTAMBLE = b'\xFF'
	ID_MAP: ClassVar[dict[int | None, bytes]] = {i: bytes([x]) for i, x in enumerate(b'IJKLMNOpqrstuvwx')}
	ID_MAP[None] = b'*'
	REVERSE_ID_MAP = {v: k for k, v in ID_MAP.items()}
	CRC = crc.Configuration(
		width=16,
		polynomial=0x8005,
		init_value=0xFFFF,
		final_xor_value=0x0000,
		reverse_input=False,
		reverse_output=False,
	)

	src_id:  int | None
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

		checksum = crc.Calculator(self.CRC).checksum(cdata)
		data = self.PREAMBLE + cdata + pack('>H', checksum) + self.POSTAMBLE
		return data

	@classmethod
	def unpack(cls, data: bytes) -> tuple['FoconFrame', bytes]:
		preamble, data = take(data, len(cls.PREAMBLE))
		if preamble != cls.PREAMBLE:
			raise ValueError(f'invalid preamble: {preamble!r}')
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
		expected_checksum = crc.Calculator(cls.CRC).checksum(cdata)

		(checksum,), data = take_unpack(data, '>H')
		if checksum != expected_checksum:
			raise ValueError(f'incorrect checksum: {checksum} != {expected_checksum}')

		postamble, data = take(data, len(cls.POSTAMBLE))
		if postamble != cls.POSTAMBLE:
			raise ValueError(f'invalid postamble: {postamble!r}')

		return cls(src_id=src_id, dest_id=dest_id, num=num, total=total, data=pdata), data

	def __repr__(self) -> str:
		s = f'{self.__class__.__name__} #{self.num}/#{self.total} {{ {self.src_id} -> {self.dest_id}'
		if self.data:
			s += f', data: {self.data.hex()}'
		s += ' }'
		return s
