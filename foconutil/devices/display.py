from typing import Iterator

from codecs import Codec, CodecInfo, charmap_encode, charmap_decode, register as register_codec
from struct import pack, unpack
from dataclasses import dataclass
from enum import Enum, Flag

from ..message import FoconMessageBus
from .device import FoconDevice, FoconDeviceInfo, dangerous, encode_version, decode_version, encode_str, decode_str


class FoconDisplayCommand(Enum):
	SelfDestruct = 0x0042
	Status       = 0x0043
	SelfTest     = 0x0044
	SetConfiguration = 0x0045
	GetConfiguration = 0x0046
	#
	SetUnk47     = 0x0047
	DrawClear    = 0x0048
	DrawPixels   = 0x0049
	DrawString   = 0x004A
	# 0x4B is not defined
	DispUnk4C    = 0x004C
	DispUnk4D    = 0x004D
	# 0x4E is not defined
	ProductInfo       = 0x004F
	ResetProductInfo  = 0x0050
	SetProductInfo    = 0x00F0
	VerifyProductInfo = 0x00F1
	#
	Info         = 0x3141
	Dump         = 0xFFF0



@dataclass
class FoconDisplayInfo(FoconDeviceInfo):
	unk08: str
	product_num: int
	unk1E: str
	unk29: str

	def pack(self) -> bytes:
		b = super().pack()

		# 0x08..0x13
		b += encode_str(self.unk08, 11)
		# 0x13..0x1E
		b += encode_str(str(self.product_num), 11)
		# 0x1E..0x29
		b += encode_str(self.unk1E, 11)
		# 0x29..0x44
		b += encode_str(self.unk29, 27)

		raise b

	@classmethod
	def unpack(cls, data: bytes) -> 'FoconDisplayInfo':
		di = FoconDeviceInfo.unpack(data)

		return cls(
			kind=di.kind,
			mode=di.mode,
			boot_version=di.boot_version,
			app_version=di.app_version,
			unk08=decode_str(data[0x08:0x13]),
			product_num=int(decode_str(data[0x13:0x1e])),
			unk1E=decode_str(data[0x1e:0x29]),
			unk29=decode_str(data[0x29:0x44]),
		)

	def __repr__(self) -> str:
		return super().__repr__().rstrip('} ') + f', unk08: {self.unk08}, product_num: {self.product_num}, unk1E: {self.unk1E}, unk29: {self.unk29} }}'

@dataclass
class FoconDisplayOutputConfiguration:
	unk00: int
	unk01: int
	unk02: int
	unk03: int
	unk04: int
	unk05: int
	row_blocks: int
	unk07: int
	total_blocks: int

	def pack(self) -> bytes:
		b = b''

		# 0x00..0x08
		b += bytes([
			self.unk00,
			self.unk01,
			self.unk02,
			self.unk03,
			self.unk04,
			self.unk05,
			self.row_blocks,
			self.unk07,
		])
		# 0x08..0x0A
		b += pack('>H', self.total_blocks)

		return b

	@classmethod
	def unpack(cls, data: bytes) -> 'FoconDisplayOutputConfiguration':
		return cls(
			unk00=data[0],
			unk01=data[1],
			unk02=data[2],
			unk03=data[3],
			unk04=data[4],
			unk05=data[5],
			row_blocks=data[6],
			unk07=data[7],
			total_blocks=unpack('>H', data[8:10])[0],
		)

	@property
	def col_blocks(self) -> int:
		return self.total_blocks // self.row_blocks

@dataclass
class FoconDisplayConfigurationUnk6C:
	data: bytes

	def pack(self) -> bytes:
		return self.data

	@classmethod
	def unpack(cls, data: bytes) -> 'FoconDisplayConfigurationUnk6C':
		return cls(data=data)

MAX_OUTPUTS = 10

@dataclass
class FoconDisplayConfiguration:
	param0: int
	param1: int
	led_col_size: int
	brightness_sensor: bool
	active_low: bool
	led_delay_us: int
	hw_loop_delay_ms: int
	brightness_mess_count:  int
	temperature_mess_count: int

	outputs: list[FoconDisplayOutputConfiguration]

	unk6C: FoconDisplayConfigurationUnk6C
	unk94: FoconDisplayConfigurationUnk6C

	unk00: int
	unkBC: int
	unkBE: int
	unkBF: int
	x_offset: int
	y_offset: int
	x_max: int
	y_max: int

	def pack(self) -> bytes:
		b = b''

		# 0x00..0x07
		b += bytes([
			self.unk00,
			1 if self.brightness_sensor else 0,   # param3
			1 if self.active_low else 0,          # param4
			self.param0,
			self.led_col_size,                    # param2
			self.param1,
			self.led_delay_us,                    # param6
			len(self.outputs),
		])
		# 0x08..0x06C
		for out in self.outputs:
			b += out.pack()
		for _ in range(MAX_OUTPUTS - len(self.outputs)):
			b += FoconDisplayOutputConfiguration.unused().pack()
		# 0x6C..0x94
		b += self.unk6C.pack()
		# 0x94..0xBC
		b += self.unk94.pack()
		# 0xBC..0xBE
		b += pack('>H', self.unkBC)
		# 0xBE..0xC2
		b += bytes([
			self.unkBE,
			self.unkBF,
			self.x_offset,
			self.y_offset,
		])
		# 0xC2..0xC4
		b += pack('>H', self.x_max)
		# 0xC4..0xC6
		b += pack('>H', self.y_max)
		# 0xC6..0xC9
		b += bytes([
			self.hw_loop_delay_ms,       # param7
			self.brightness_mess_count,  # param8
			self.temperature_mess_count, # param9
		])

		return b

	@classmethod
	def unpack(cls, data: bytes) -> 'FoconDisplayConfiguration':
		return cls(
			param0=data[0x03],
			param1=data[0x05],
			led_col_size=data[0x04], # param2
			brightness_sensor=bool(data[0x01]), # param3
			active_low=bool(data[0x02]), # param4
			led_delay_us=data[0x06], # param6
			hw_loop_delay_ms=data[0xC6], # param7
			brightness_mess_count=data[0xC7], # param8
			temperature_mess_count=data[0xC8], # param9

			outputs=[
				FoconDisplayOutputConfiguration.unpack(data[8 + i * 10:8 + i * 10 + 10])
				for i in range(data[7])
			],

			unk6C=FoconDisplayConfigurationUnk6C.unpack(data[0x6C:0x94]),
			unk94=FoconDisplayConfigurationUnk6C.unpack(data[0x94:0xBC]),

			unk00=data[0],
			unkBC=unpack('>H', data[0xBC:0xBE])[0],
			unkBE=data[0xBE],
			unkBF=data[0xBF],
			x_offset=data[0xC0],
			y_offset=data[0xC1],
			x_max=unpack('>H', data[0xC2:0xC4])[0],
			y_max=unpack('>H', data[0xC4:0xC6])[0],
		)

	@property
	def leds_per_col_block(self) -> int:
		return 1 << (self.led_col_size + 2)

	@property
	def leds_per_row_block(self) -> int:
		return 16

	@property
	def width(self) -> int:
		if (self.x_offset, self.y_offset, self.x_max, self.y_max) != (0, 0, 0, 0):
			return self.x_max - self.x_offset + 1
		entry = self.outputs[0]
		return entry.col_blocks * self.leds_per_col_block

	@property
	def height(self) -> int:
		if (self.x_offset, self.y_offset, self.x_max, self.y_max) != (0, 0, 0, 0):
			return self.y_max - self.y_offset + 1
		entry = self.outputs[0]
		return entry.row_blocks * self.leds_per_row_block

class FoconDisplayDumpType(Enum):
	MemoryStats = 0x01
	NetworkStats = 0x02
	EnvironmentBrightness = 0x03
	Unk04 = 0x04
	Unk05 = 0x05
	TaskStats = 0x06

@dataclass
class FoconDisplayProductInfo:
	boot_version: tuple[int, int]
	num:        int
	name:       str
	unk1_count: int
	unk1_value: int

	def pack(self) -> bytes:
		raise NotImplementedError()

	@classmethod
	def unpack(cls, data: bytes) -> 'FoconDisplayProductInfo':
		return cls(
			boot_version=decode_version(data[0:3]),
			num=int(decode_str(data[4:14])),
			name=decode_str(data[14:64]),
			unk1_count=data[64],
			unk1_value=unpack('>I', data[66:70])[0],
		)


class FoconDisplaySelfTestKind(Enum):
	Info = 1
	Flood = 2
	Abort = 3

class FoconDisplayError(Flag):
	Unk00         = (1 << 0)
	Watchdog      = (1 << 1)
	Memory        = (1 << 2)
	Temperature   = (1 << 3)
	DisplayDraw   = (1 << 4)
	Configuration = (1 << 5)
	DisplayDriver = (1 << 6)
	Power10       = (1 << 7)
	ConfigBE      = (1 << 8)
	ProductInfo   = (1 << 9)
	Unk10         = (1 << 10)
	Option1       = (1 << 11)
	Option2       = (1 << 12)
	Option3       = (1 << 13)
	Option4       = (1 << 14)
	Option5       = (1 << 15)

@dataclass
class FoconDisplayStatus:
	error_flags:              FoconDisplayError
	temperature:              float
	mode:                     int
	brightness_average:       int | None
	unk1_3:                   int
	hw_ipc_val_3:             int
	hw_ipc_val_res:           int
	sensor4_value:            int
	available_still_objects:  int
	available_scroll_objects: int
	unk2a:                    bytes | None
	unk2b:                    bytes | None

	@classmethod
	def unpack(cls, data: bytes) -> 'FoconDisplayStatus':
		return cls(
			error_flags=FoconDisplayError(unpack('>H', data[0:2])[0]),
			temperature=unpack('>H', data[2:4])[0] / 10,
			mode=data[4], # status0
			sensor4_value=data[5], # status6
			brightness_average=data[6] if bool(data[10]) else None, # status2, status1
			hw_ipc_val_3=data[7], # status4
			unk1_3=data[8],
			hw_ipc_val_res=data[9], # status5
			available_still_objects=data[11], # status7
			available_scroll_objects=data[12], # status8
			unk2a=data[15:38] if bool(data[14]) else None,
			unk2b=data[39:62] if bool(data[38]) else None,
		)

class FoconDisplayDrawComposition(Enum):
	Replace = 'N'
	Add = 'A'
	UnkO = 'O'

	@classmethod
	def parse(cls, s: str) -> 'FoconDisplayDrawComposition':
		return COMPOSITION_NAMES[s]

COMPOSITION_NAMES = {
	'none': FoconDisplayDrawComposition.Replace,
	'replace': FoconDisplayDrawComposition.Replace,
	'add': FoconDisplayDrawComposition.Add,
}

class FoconDisplayObjectEffect(Enum):
	UnkU = 'U'
	UnkD = 'D'
	LeftScroll = 'L'
	RightScroll = 'R'
	Appear = 'A'
	Disappear = 'B'
	Blink = 'V'

	@classmethod
	def parse(cls, s: str) -> 'FoconDisplayObjectEffect':
		return EFFECT_NAMES[s]

EFFECT_NAMES = {
	'scroll': FoconDisplayObjectEffect.LeftScroll,
	'left-scroll': FoconDisplayObjectEffect.LeftScroll,
	'right-scroll': FoconDisplayObjectEffect.RightScroll,
	'appear': FoconDisplayObjectEffect.Appear,
	'none': FoconDisplayObjectEffect.Appear,
	'disappear': FoconDisplayObjectEffect.Disappear,
	'blink': FoconDisplayObjectEffect.Blink,
}


REVERSE_CHARSET = {x: ord(bytes([x]).decode('cp850')) for x in range(256)}
REVERSE_CHARSET[0xA7] = ord('✈')
REVERSE_CHARSET[0xAE] = ord('←')
REVERSE_CHARSET[0xAF] = ord('→')
REVERSE_CHARSET[0xB0] = ord('º')
CHARSET = {c: i for i, c in REVERSE_CHARSET.items()}

class Focon850(Codec):
	NAME = 'focon_train_cp850'

	def encode(self, input: str, errors: str = 'strict') -> tuple[bytes, int]:
		return charmap_encode(input, errors, CHARSET)

	def decode(self, input: bytes, errors: str = 'strict') -> tuple[str, int]:
		return charmap_decode(input, errors, REVERSE_CHARSET)

	@classmethod
	def lookup(cls, name: str) -> CodecInfo | None:
		if name == cls.NAME:
			codec = cls()
			return CodecInfo(name=name, encode=codec.encode, decode=codec.decode)
		return None

register_codec(Focon850.lookup)


@dataclass
class FoconDisplayObject:
	object_id:   int
	output_id:   int
	unk0E:       int
	unk0F:       int
	composition: FoconDisplayDrawComposition
	x_end:       int
	y_end:       int
	x_start:     int = 0
	y_start:     int = 0
	effect:      FoconDisplayObjectEffect = FoconDisplayObjectEffect.Appear
	count:       int = 1
	delay:       int = 1
	data:        bytes = b''

	def pack(self) -> bytes:
		return (bytes([self.object_id, ord(self.composition.value)]) +
		        pack('>HHHH', self.x_start, self.y_start, self.x_end, self.y_end) +
		        bytes([ord(self.effect.value), self.count, self.output_id, self.delay, self.unk0E, self.unk0F]) +
		        self.data)

	@classmethod
	def unpack(cls, data: bytes) -> 'FoconDisplayObject':
		x_start, y_start, x_end, y_end = unpack('>HHHH', data[2:10])
		return cls(
			object_id=data[0],
			composition=FoconDisplayDrawComposition(chr(data[1])),
			x_start=x_start,
			y_start=y_start,
			x_end=x_end,
			y_end=y_end,
			effect=FoconDisplayObjectEffect(chr(data[10])),
			count=data[11],
			output_id=data[12],
			delay=data[13],
			unk0E=data[14],
			unk0F=data[15],
			data=data[16:],
		)

	@classmethod
	def make_string_data(cls, message: str, flags: int = 4, font_id: int = 16) -> bytes:
		return bytes([flags, font_id]) + message.encode(Focon850.NAME) + b'\x00'

	@classmethod
	def make_pixel_data(cls, data: bytes, width: int = 6, height: int = 12) -> bytes:
		return pack('>HH', height, width) + data



class FoconDisplay:
	device: FoconDevice
	current_config: FoconDisplayConfiguration = None

	def __init__(self, device: FoconDevice) -> None:
		self.device = device
		self.current_config = None

	def get_current_config(self) -> FoconDisplayConfiguration:
		if not self.current_config:
			self.current_config = self.get_config()
		return self.current_config

	def use_config(self, config: FoconDisplayConfiguration) -> None:
		self.current_config = config


	def send_command(self, command: FoconDisplayCommand, payload: bytes = b'') -> bytes:
		return self.device.send_command(command.value, payload=payload)


	def parse_dump_response(self, type: FoconDisplayDumpType, response: bytes) -> str:
		if response[0] != type.value:
			raise ValueError(f'invalid dump response type: {response[0]} != {type}')
		return decode_str(response[2:])

	def do_dump(self, type: FoconDisplayDumpType) -> str:
		response = self.send_command(FoconDisplayCommand.Dump, bytes([type.value, 0x00]))
		return self.parse_dump_response(type, response)

	def recv_dump_messages(self, type: FoconDisplayDumpType) -> Iterator[str]:
		for msg in self.device.recv_messages(cmd=FoconDisplayCommand.Dump.value):
			yield self.parse_dump_response(type, msg.value)

	def get_device_info(self) -> FoconDeviceInfo:
		return self.device.get_device_info()


	def print(self, message: str, composition: FoconDisplayDrawComposition = None, effect: FoconDisplayObjectEffect = None) -> bytes:
		config = self.get_current_config()
		cmd = FoconDisplayObject(
			object_id=0xFF,
			output_id=1,
			composition=composition or FoconDisplayDrawComposition.Replace,
			effect=effect or FoconDisplayObjectEffect.Appear,
			x_end=config.x_max,
			y_end=config.y_max,
			unk0E=255,
			unk0F=81,
			data=FoconDisplayObject.make_string_data(message),
		)
		return self.send_command(FoconDisplayCommand.DrawString, cmd.pack())

	@dangerous
	def self_destruct(self) -> None:
		self.send_command(FoconDisplayCommand.SelfDestruct)

	def get_status(self) -> FoconDisplayStatus:
		response = self.send_command(FoconDisplayCommand.Status)
		return FoconDisplayStatus.unpack(response)

	def trigger_selftest(self, type: FoconDisplaySelfTestKind) -> bool:
		response = self.send_command(FoconDisplayCommand.SelfTest, bytes([type.value, 0x00]))
		if response[0] != type.value:
			raise ValueError(f'got invalid selftest type response {response[0]} != {type}')
		return response[1] == 0xff

	def get_config(self) -> FoconDisplayConfiguration:
		response = self.send_command(FoconDisplayCommand.GetConfiguration)
		return FoconDisplayConfiguration.unpack(response)

	@dangerous
	def set_config(self, config: FoconDisplayConfiguration) -> None:
		response = self.send_command(FoconDisplayCommand.SetConfiguration, config.pack())

	@dangerous
	def set_unk47(self, p1: int, p2: int) -> None:
		self.send_command(FoconDisplayCommand.SetUnk47, bytes([p1, p2]))

	def get_product_info(self) -> FoconDisplayProductInfo:
		response = self.send_command(FoconDisplayCommand.ProductInfo)
		return FoconDisplayProductInfo.unpack(response)

	@dangerous
	def reset_product_info(self) -> None:
		self.send_command(FoconDisplayCommand.ResetProductInfo)

	def verify_product_info(self) -> None:
		self.send_command(FoconDisplayCommand.VerifyProductInfo)

	@dangerous
	def set_product_info(self, info: FoconDisplayProductInfo) -> None:
		self.send_command(FoconDisplayCommand.SetProductInfo, info.pack())

	def get_display_info(self) -> FoconDisplayInfo:
		response = self.send_command(FoconDisplayCommand.Info)
		return FoconDisplayInfo.unpack(response)

	def get_memory_stats(self) -> str:
		return self.do_dump(FoconDisplayDumpType.MemoryStats)

	def get_network_stats(self) -> str:
		return self.do_dump(FoconDisplayDumpType.NetworkStats)

	def get_task_stats(self) -> Iterator[str]:
		self.do_dump(FoconDisplayDumpType.TaskStats)
		yield from self.recv_dump_messages(FoconDisplayDumpType.TaskStats)

	def get_sensor_stats(self) -> str:
		return self.do_dump(FoconDisplayDumpType.EnvironmentBrightness)
