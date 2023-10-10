from enum import Enum

from .device import FoconDevice, dangerous


class FoconBootCommand(Enum):
	WriteFirmware  = 0x00F0
	VerifyFirmware = 0x00F1

class FoconBootDevice(FoconDevice):
	def send_boot_command(self, command: FoconBootCommand, payload: bytes = b'') -> bytes:
		return self.bus.send_command(self.dest_id, command.value, payload=payload)

	def verify_firmware(self) -> None:
		self.send_boot_command(FoconBootCommand.VerifyFirmware)

	@dangerous
	def write_firmware(self, data: bytes) -> None:
		self.send_boot_command(FoconBootCommand.WriteFirmware, data)
