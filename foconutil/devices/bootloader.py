from enum import Enum
from dataclasses import dataclass
from struct import pack

from .device import FoconDevice, FoconDeviceInfo, dangerous


class FoconBootCommand(Enum):
	WriteFlash = 0x00F0
	LaunchApp  = 0x00F1

@dataclass
class FoconBootFlashBlock:
	address: int
	data: bytes

	def pack(self) -> bytes:
		return pack('>HI', len(self.data), self.address) + self.data

class FoconBootDevice:
	APP_ADDRESS = 0x7000

	def __init__(self, device: FoconDevice) -> None:
		self.device = device

	def send_boot_command(self, command: FoconBootCommand, payload: bytes = b'') -> bytes:
		return self.device.send_command(command.value, payload=payload)


	def get_device_info(self) -> FoconDeviceInfo:
		return self.device.get_device_info()

	def launch(self) -> bool:
		reply = self.send_boot_command(FoconBootCommand.LaunchApp)
		return reply[0] == 1

	@dangerous
	def write_flash(self, address: int, data: bytes) -> int:
		chunk_size = 0x200
		for off in range(0, len(data), chunk_size):
			print(hex(off))
			block = FoconBootFlashBlock(address=address + off, data=data[off:off + chunk_size])
			status = self.send_boot_command(FoconBootCommand.WriteFlash, block.pack())
			if not status[0]:
				raise ValueError('flashing address 0x{:08x} failed!'.format(address + off))

	@dangerous
	def write_app(self, data: bytes) -> None:
		return self.write_flash(self.APP_ADDRESS, data)
