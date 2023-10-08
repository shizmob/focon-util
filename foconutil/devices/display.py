from typing import Callable, Iterator, Any
from struct import unpack
from dataclasses import dataclass
from enum import Enum, Flag

from ..message import FoconMessageBus


class FoconDisplayCommand(Enum):
	BootInfo     = 0x0041
	SelfDestruct = 0x0042
	Status       = 0x0043
	SelfTest     = 0x0044
	SetConfiguration = 0x0045
	GetConfiguration = 0x0046
	#
	SetUnk47     = 0x0047
	DispUnk48    = 0x0048
	DispUnk49    = 0x0049
	DispUnk4A    = 0x004A
	# 0x4B is not defined
	DispUnk4C    = 0x004C
	DispUnk4D    = 0x004D
	# 0x4E is not defined
	ProductInfo       = 0x004F
	ResetProductInfo  = 0x0050
	SetProductInfo    = 0x00F0
	VerifyProductInfo = 0x00F1
	#
	ExtendedInfo = 0x3141
	Dump         = 0xFFF0


def decode_version(data: bytes) -> tuple[int, int]:
	return int(data[0:1].decode('ascii'), 10), int(data[1:3].decode('ascii'), 10)

def decode_str(data: bytes) -> str:
	if b'\0' in data:
		data = data[:data.index(b'\0')]
	return data.decode('iso-8859-15')

@dataclass
class FoconDisplayBootInfo:
	kind: str
	boot_version: tuple[int, int]
	app_version: tuple[int, int]

	def pack(self) -> bytes:
		raise NotImplementedError()

	@classmethod
	def unpack(cls, data: bytes) -> 'FoconDisplayBootInfo':
		return cls(
			kind=data[0:2].decode('ascii'),
			boot_version=decode_version(data[2:5]),
			app_version=decode_version(data[5:8]),
		)

	def __repr__(self) -> str:
		return f'{self.__class__.__name__} {{ {self.kind}, boot: {self.boot_version[0]}.{self.boot_version[1]:02}, app: {self.app_version[0]}.{self.app_version[1]:02} }}'

@dataclass
class FoconDisplayExtInfo(FoconDisplayBootInfo):
	unk08: str
	product_num: int
	unk1E: str
	unk29: str

	def pack(self) -> bytes:
		raise NotImplementedError()

	@classmethod
	def unpack(cls, data: bytes) -> 'FoconDisplayExtInfo':
		di = FoconDisplayBootInfo.unpack(data)

		return cls(
			kind=di.kind,
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

	@classmethod
	def unpack(cls, data: bytes) -> 'FoconDisplayConfigurationUnk6C':
		return cls(data=data)

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

	unkBC: int
	unkBE: int
	unkBF: int
	x_offset: int
	y_offset: int
	x_max: int
	y_max: int

	def pack(self) -> bytes:
		raise NotImplementedError()

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
	err_status:  FoconDisplayError
	temperature: int
	mode:        int
	brightness_sensor: bool
	average_brightness: int
	unk1_3:      int
	hw_ipc_val_3: int
	hw_ipc_val_res: int
	sensor4_value: int
	unk11_avail: int
	unk12_avail: int
	unk2a_valid: int
	unk2a_value: bytes
	unk2b_valid: int
	unk2b_value: bytes

	@classmethod
	def unpack(cls, data: bytes) -> 'FoconDisplayStatus':
		return cls(
			err_status=FoconDisplayError(unpack('>H', data[0:2])[0]),
			temperature=unpack('>H', data[2:4])[0] / 10,
			mode=data[4], # status0
			sensor4_value=data[5], # status6
			average_brightness=data[6], # status2
			hw_ipc_val_3=data[7], # status4
			unk1_3=data[8],
			hw_ipc_val_res=data[9], # status5
			brightness_sensor=bool(data[10]), # status1
			unk11_avail=data[11], # status7
			unk12_avail=data[12], # status8
			unk2a_valid=bool(data[14]),
			unk2a_value=data[15:38],
			unk2b_valid=bool(data[38]),
			unk2b_value=data[39:62],
		)

def dangerous(fn: Callable[..., Any]) -> Callable[..., Any]:
	return fn

class FoconDisplay:
	def __init__(self, bus: FoconMessageBus, dest_id: int) -> None:
		self.bus = bus
		self.dest_id = dest_id

	def send_command(self, command: FoconDisplayCommand, payload: bytes = b'') -> bytes:
		return self.bus.send_command(self.dest_id, command.value, payload=payload)

	def parse_dump_response(self, type: FoconDisplayDumpType, response: bytes) -> str:
		if response[0] != type.value:
			raise ValueError(f'invalid dump response type: {response[0]} != {type}')
		return decode_str(response[2:])

	def do_dump(self, type: FoconDisplayDumpType) -> str:
		response = self.send_command(FoconDisplayCommand.Dump, bytes([type.value, 0x00]))
		return self.parse_dump_response(type, response)

	def recv_dump_message(self, type: FoconDisplayDumpType) -> str:
		response = self.bus.recv_message(cmd=FoconDisplayCommand.Dump.value).value
		return self.parse_dump_response(type, response)


	def get_boot_info(self) -> FoconDisplayBootInfo:
		response = self.send_command(FoconDisplayCommand.BootInfo)
		return FoconDisplayBootInfo.unpack(response)

	@dangerous
	def self_destruct(self) -> None:
		self.send_command(FoconDisplayCommand.SelfDestruct)

	def get_status(self) -> FoconDisplayStatus:
		response = self.send_command(FoconDisplayCommand.Status)
		return FoconDisplayStatus.unpack(response)

	def trigger_selftest(self, type: int) -> bool:
		response = self.send_command(FoconDisplayCommand.SelfTest, bytes([type, 0x00]))
		if response[0] != type:
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

	def verify_product_info(self) -> None:
		self.send_command(FoconDisplayCommand.VerifyProductInfo)

	@dangerous
	def set_product_info(self, info: FoconDisplayProductInfo) -> None:
		self.send_command(FoconDisplayCommand.SetProductInfo, info.pack())

	@dangerous
	def reset_product_info(self) -> None:
		self.send_command(FoconDisplayCommand.ResetProductInfo)

	def get_ext_info(self) -> FoconDisplayExtInfo:
		response = self.send_command(FoconDisplayCommand.ExtendedInfo)
		return FoconDisplayExtInfo.unpack(response)

	def get_memory_stats(self) -> str:
		return self.do_dump(FoconDisplayDumpType.MemoryStats)

	def get_network_stats(self) -> str:
		return self.do_dump(FoconDisplayDumpType.NetworkStats)

	def get_task_stats(self) -> Iterator[str]:
		yield self.do_dump(FoconDisplayDumpType.TaskStats)
		while True:
			yield self.recv_dump_message(FoconDisplayDumpType.TaskStats)

	def get_sensor_stats(self) -> str:
		return self.do_dump(FoconDisplayDumpType.EnvironmentBrightness)
