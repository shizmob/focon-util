from enum import Enum

from .device import FoconDevice, FoconDeviceInfo, dangerous


class FoconBootCommand(Enum):
	WriteFlash = 0x00F0
	LaunchApp  = 0x00F1

class FoconBootFlashBlock:
	address: int
	data: bytes

	def pack(self) -> bytes:
		return pack('>HI', len(self.data), self.address) + data

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
		block = FoconBootFlashBlock(address=address, data=data)
		reply = self.send_boot_command(FoconBootCommand.WriteFlash, block.pack())
		return reply[0]

	@dangerous
	def write_app(self, data: bytes) -> None:
		return self.write_flash(self.APP_ADDRESS, data)
