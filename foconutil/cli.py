import argparse
import logging
import time
try:
	import PIL.Image
except ImportError:
	# Not mandatory
	PIL = None

from . import FoconFrame, FoconSerialTransport, FoconBus, FoconMessageBus, FoconDisplay
from .devices.bootloader import FoconBootDevice
from .devices.display import *


def main() -> None:
	p = argparse.ArgumentParser()
	p.add_argument('-d', '--device', default='/dev/ttyUSB0', help='bus device')
	p.add_argument('-b', '--baudrate', type=int, help='bus baud rate')
	p.add_argument('-x', '--crystal', type=float, help='crystal oscillator frequency')
	p.add_argument('--flow-control', action='store_true', default=False, help='enable hardware flow control')
	p.add_argument('-D', '--debug', action='count', default=0, help='debug log')
	p.add_argument('-s', '--source-id', type=int, default=14, help='source device ID')
	p.add_argument('-i', '--id', type=int, default=0, help='device ID')
	p.set_defaults(_handler=None)

	subcommands = p.add_subparsers(title='subcommands', required=True)


	# General subcommands

	def do_info(args):
		transport = FoconSerialTransport(args.device, baudrate=args.baudrate, xtal=args.crystal, flow_control=args.flow_control, debug=args.debug > 2)
		bus = FoconBus(transport, args.source_id, debug=args.debug > 1)
		msg_bus = FoconMessageBus(bus, args.source_id, debug=args.debug > 0)
		device = FoconDevice(msg_bus, args.id)
		device_info = device.get_device_info()
		print('boot:')
		print('  mode:   ', device_info.mode.name.lower())
		print('  type:   ', device_info.kind)
		print('  version: {}.{:02}'.format(*device_info.boot_version))
		print()

		if device_info.app_version:
			print('app:')
			print('  version: {}.{:02}'.format(*device_info.app_version))
			print()
	info_parser = subcommands.add_parser('info')
	info_parser.set_defaults(_handler=do_info)

	# Bootloader subcommands

	def do_bootloader(args):
		transport = FoconSerialTransport(args.device, baudrate=args.baudrate, xtal=args.crystal, flow_control=args.flow_control, debug=args.debug > 2)
		bus = FoconBus(transport, args.source_id, debug=args.debug > 1)
		msg_bus = FoconMessageBus(bus, args.source_id, debug=args.debug > 0)
		device = FoconDevice(msg_bus, args.id)
		bootloader = FoconBootDevice(device)

		args._bootloader_handler(bootloader, args)
	bootloader_parser = subcommands.add_parser('boot')
	bootloader_parser.set_defaults(_handler=do_bootloader, _bootloader_handler=None)
	bootloader_subcommands = bootloader_parser.add_subparsers(title='boot loader subcommands', required=True)

	def do_flash_app(bootloader, args):
		for offset in bootloader.write_app(args.APP.read()):
			print('Flashing: {:08x}...'.format(offset))

	flash_app_parser = bootloader_subcommands.add_parser('flash')
	flash_app_parser.add_argument('APP', type=argparse.FileType('rb'))
	flash_app_parser.set_defaults(_bootloader_handler=do_flash_app)

	def do_flash_block(bootloader, args):
		for offset in bootloader.write_flash(args.ADDRESS, args.DATA.read()):
			print('Flashing: {:08x}...'.format(offset))

	flash_block_parser = bootloader_subcommands.add_parser('flash-block')
	flash_block_parser.add_argument('ADDRESS', type=int, help='address to flash')
	flash_block_parser.add_argument('DATA', type=argparse.FileType('rb'))
	flash_block_parser.set_defaults(_bootloader_handler=do_flash_block)

	def do_launch(bootloader, args):
		if not bootloader.launch():
			return 1

	launch_parser = bootloader_subcommands.add_parser('launch')
	launch_parser.set_defaults(_bootloader_handler=do_launch)

	# Display subcommands

	def do_display(args):
		transport = FoconSerialTransport(args.device, baudrate=args.baudrate, xtal=args.crystal, flow_control=args.flow_control, debug=args.debug > 2)
		bus = FoconBus(transport, args.source_id, debug=args.debug > 1)
		msg_bus = FoconMessageBus(bus, args.source_id, debug=args.debug > 0)
		device = FoconDevice(msg_bus, args.id)
		display = FoconDisplay(device)

		args._display_handler(display, args)
	display_parser = subcommands.add_parser('display')
	display_parser.set_defaults(_handler=do_display, _display_handler=None)
	display_subcommands = display_parser.add_subparsers(title='display subcommands', required=True)

	def do_display_info(display, args):
		device_info = display.get_display_info()
		print('boot:')
		print('  type:   ', device_info.kind)
		print('  mode:   ', device_info.mode.name)
		print('  version: {}.{:02}'.format(*device_info.boot_version))
		print()

		print('app:')
		print('  version: {}.{:02}'.format(*device_info.app_version))
		print()

		print('display:')
		if device_info.unk08:
			print('  unk08:  ', device_info.unk08)
		if device_info.part_id:
			print('  part:   ', device_info.part_id)
		if device_info.unk1E:
			print('  unk1E:  ', device_info.unk1E)
		if device_info.unk29:
			print('  unk29:  ', device_info.unk29)
		print()

		print('assets:')
		asset_data = display.get_asset_data()
		print('  part:   ', asset_data.part_id)
		print('  name:   ', asset_data.name)
		print('  version: {}.{:02}'.format(*asset_data.version))
		print('  size:   ', asset_data.size)
		print('  fonts:')
		for font_id in range(asset_data.font_count):
			print('    - font')
		print()

		print('stats:')
		print('  memory: ', display.get_memory_stats())
		print('  network:', display.get_network_stats())
		print('  sensors:', display.get_sensor_stats())
		print()

		print('tasks:')
		for t in display.get_task_stats():
			print('  ' + t)

	get_info_parser = display_subcommands.add_parser('info')
	get_info_parser.set_defaults(_display_handler=do_display_info)

	def do_display_get_config(display, args):
		print(display.get_current_config())
	get_config_parser = display_subcommands.add_parser('get-config')
	get_config_parser.set_defaults(_display_handler=do_display_get_config)

	def do_display_memory_stats(display, args):
		print(display.get_memory_stats())
	get_memory_stats_parser = display_subcommands.add_parser('memory-stats')
	get_memory_stats_parser.set_defaults(_display_handler=do_display_memory_stats)

	def do_display_network_stats(display, args):
		print(display.get_network_stats())
	get_network_stats_parser = display_subcommands.add_parser('network-stats')
	get_network_stats_parser.set_defaults(_display_handler=do_display_network_stats)

	def do_display_sensor_stats(display, args):
		print(display.get_sensor_stats())
	get_sensor_stats_parser = display_subcommands.add_parser('sensor-stats')
	get_sensor_stats_parser.set_defaults(_display_handler=do_display_sensor_stats)

	def do_display_task_stats(display, args):
		for stat in display.get_task_stats():
			print('*', stat)
	get_task_stats_parser = display_subcommands.add_parser('task-stats')
	get_task_stats_parser.set_defaults(_display_handler=do_display_task_stats)

	SELFTEST_TYPES = {
		'info': FoconDisplaySelfTestKind.Info,
		'flood': FoconDisplaySelfTestKind.Flood,
		'abort': FoconDisplaySelfTestKind.Abort,
	}
	def do_display_selftest(display, args):
		print(display.trigger_selftest(SELFTEST_TYPES[args.type]))
	selftest_parser = display_subcommands.add_parser('selftest')
	selftest_parser.set_defaults(_display_handler=do_display_selftest)
	selftest_parser.add_argument('type', choices=tuple(SELFTEST_TYPES))

	def do_display_selfdestruct(display, args):
		print(display.self_destruct())
	selfdestruct_parser = display_subcommands.add_parser('selfdestruct')
	selfdestruct_parser.set_defaults(_display_handler=do_display_selfdestruct)

	def do_display_status(display, args):
		print(display.get_status())
	get_status_parser = display_subcommands.add_parser('status')
	get_status_parser.set_defaults(_display_handler=do_display_status)

	def do_display_product_info(display, args):
		print(display.get_product_info())
	get_product_info_parser = display_subcommands.add_parser('product-info')
	get_product_info_parser.set_defaults(_display_handler=do_display_product_info)

	# Display drawing commands

	def do_display_draw_base(display, args):
		# Obtain (and store) config if needed
		config = None
		if args.config:
			args.config.seek(0)
			try:
				config = FoconDisplayConfiguration.unpack(args.config.read())
			except:
				print('display configuration was corrupted, re-reading')

		if not config:
			config = display.get_current_config()
			if args.config:
				args.config.truncate(0)
				args.config.write(config.pack())

		display.use_config(config)
		return args._display_draw_handler(display, args)

	def add_display_draw_args(parser):
		parser.add_argument('-c', '--config', type=argparse.FileType('a+b'), metavar='FILE', help='path to file containing display configuration to use (will be written if specified but empty or invalid)')
		parser.add_argument('-C', '--composition', type=FoconDisplayDrawComposition.parse, help='layer composition for drawing object') #choices=list(COMPOSITION_NAMES))
		parser.add_argument('-T', '--transition', type=FoconDisplayDrawTransition.parse, help='effect for drawing object') #, choices=list(EFFECT_NAMES))
		parser.set_defaults(_display_handler=do_display_draw_base, _display_draw_handler=None)

	def do_display_draw_object(display, args):
		config = display.get_current_config()

		# build object spec
		output_ids = args.output_id or [1]
		x = args.x if args.x is not None else config.x_start
		y = args.y if args.y is not None else config.y_start
		width = args.width if args.width is not None else (config.x_end - x + 1)
		height = args.height if args.height is not None else (config.y_end - y + 1)
		for output_id in output_ids:
			spec = FoconDisplayDrawSpec(
				object_id=args.object_id,
				output_id=output_id,
				composition=args.composition or FoconDisplayDrawComposition.Replace,
				transition=args.transition or FoconDisplayDrawTransition.Appear,
				x_start=x,
				y_start=y,
				x_end=(x + width) - 1,
				y_end=(y + height) - 1,
				count=args.count or 1,
				duration=args.duration or 10,
			)
			r = args._display_draw_object_handler(display, spec, args)
			if r not in (None, 0):
				sys.exit(r)

	def parse_range(s: str):
		if ':' in s:
			start, end = s.split(':', 1)
			return (int(start), int(end))
		else:
			return int(s)

	def parse_alignment(s: str):
		if '-' in s:
			vs, hs = s.split('-', maxsplit=1)
			va = FoconDisplayVerticalAlignment(vs)
			ha = FoconDisplayHorizontalAlignment(hs)
		elif s == 'center':
			va = FoconDisplayVerticalAlignment(s)
			ha = FoconDisplayHorizontalAlignment(s)
		elif s in FoconDisplayVerticalAlignment:
			va = FoconDisplayVerticalAlignment(s)
			ha = FoconDisplayVerticalAlignment.Center
		elif s in FoconDisplayHorizontalAlignment:
			va = FoconDisplayVerticalAlignment.Center
			ha = FoconDisplayHorizontalAlignment(s)
		else:
			raise ValueError('invalid alignment value: {}'.format(s))
		return FoconDisplayAlignment(vertical=va, horizontal=ha)

	def add_display_draw_object_args(parser):
		add_display_draw_args(parser)
		parser.add_argument('-n', '--count', type=int, metavar='N', help='repetitions of object effect')
		parser.add_argument('-t', '--duration', type=int, metavar='TIME', help='time to display object for')
		parser.add_argument('-i', '--object-id', type=int, default=0xFF, metavar='ID', help='object ID')
		parser.add_argument('-o', '--output-id', action='append', type=int, metavar='ID', help='output ID(s)')
		parser.add_argument('-x', '--x', type=int, help='X position')
		parser.add_argument('-W', '--width', type=int, help='X size')
		parser.add_argument('-y', '--y', type=int, help='Y position')
		parser.add_argument('-H', '--height', type=int, help='Y size')
		parser.set_defaults(_display_draw_handler=do_display_draw_object, _display_draw_object_handler=None)

	def do_display_clear(display, args):
		for output_id in args.OUTPUT or [None]:
			print(display.clear(output_id or None, x=args.x, y=args.y))

	clear_parser = display_subcommands.add_parser('clear')
	add_display_draw_args(clear_parser)
	clear_parser.set_defaults(_display_draw_handler=do_display_clear)
	clear_parser.add_argument('-x', '--x', type=parse_range, help='X area')
	clear_parser.add_argument('-y', '--y', type=parse_range, help='Y area')
	clear_parser.add_argument('OUTPUT', nargs='*')

	def do_display_print(display, spec, args):
		print(display.print(args.message, spec=spec, font_size=args.font_size, alignment=args.alignment))

	print_parser = display_subcommands.add_parser('print')
	add_display_draw_object_args(print_parser)
	print_parser.set_defaults(_display_draw_object_handler=do_display_print)
	print_parser.add_argument('-a', '--alignment', type=parse_alignment, help='text alignment')
	print_parser.add_argument('-s', '--font-size', type=int, metavar='SIZE', help='text size')
	print_parser.add_argument('message')

	def do_display_draw(display, spec, args):
		image = PIL.Image.open(args.file)
		n_frames = getattr(image, 'n_frames', 1)
		loops = image.info.get('loop', 1)

		n = 0
		epoch = time.time()
		frames = []
		while loops == 0 or n < loops:
			for frame_id in range(n_frames):
				start = time.time()
				image.seek(frame_id)
				frame_duration = image.info.get('duration', 0) / 1000

				if frame_id < len(frames):
					frame = frames[frame_id]
				else:
					if image.mode != '1':
						f = image.convert('1')
					else:
						f = image
					frame = []
					for x in range(f.width):
						frame.append([bool(f.getpixel((x, y))) for y in range(f.height)])
					if loops != 1:
						frames.append(frame)

				display.draw(frame, f.height, spec)
				end = time.time()

				elapsed = end - start
				if elapsed < frame_duration:
					time.sleep((frame_duration - elapsed) / 2)
				if frame_id > 0:
					print('\rFPS: {:4.2f}, data rate: {:.2f} b/s'.format(
						(n * n_frames + frame_id + 1)  / (end - epoch),
						8 * display.device.bus.bus.transport.n / (end - epoch),
					), end='')

			n += 1

	draw_parser = display_subcommands.add_parser('draw')
	add_display_draw_object_args(draw_parser)
	draw_parser.set_defaults(_display_draw_object_handler=do_display_draw)
	draw_parser.add_argument('file', type=argparse.FileType('rb'))

	def do_display_fill(display, spec, args):
		print(display.fill(spec, bool(args.VALUE)))

	fill_parser = display_subcommands.add_parser('fill')
	add_display_draw_object_args(fill_parser)
	fill_parser.set_defaults(_display_draw_object_handler=do_display_fill)
	fill_parser.add_argument('VALUE', type=int, nargs='?', default=1)

	def do_display_redraw(display, args):
		print(display.redraw(args.ID, composition=args.composition))

	redraw_parser = display_subcommands.add_parser('redraw')
	add_display_draw_args(redraw_parser)
	redraw_parser.set_defaults(_display_draw_handler=do_display_redraw)
	redraw_parser.add_argument('ID', default=[255], type=int, nargs='*')

	def do_display_undraw(display, args):
		print(display.undraw(args.ID, update_screen=args.update))

	undraw_parser = display_subcommands.add_parser('undraw')
	add_display_draw_args(undraw_parser)
	undraw_parser.set_defaults(_display_draw_handler=do_display_undraw)
	undraw_parser.add_argument('ID', default=[255], type=int, nargs='*')
	undraw_parser.add_argument('-N', '--no-update', action='store_false', dest='update', default=True)

	def do_display_flood(display, args):
		print(display.flood())
	flood_parser = display_subcommands.add_parser('flood')
	add_display_draw_args(flood_parser)
	flood_parser.set_defaults(_display_draw_handler=do_display_flood)

	# Debug commands

	debug_parser = subcommands.add_parser('debug')
	debug_subcommands = debug_parser.add_subparsers(title='debug subcommands', required=True)

	def do_self_test(args):
		class FoconMockBus(FoconBus):
			def __init__(self, frames: list[FoconFrame]) -> None:
				self.frames = frames

			def send_message(self, dest_id: int | None, data: bytes) -> None:
				pass

			def recv_message(self, peer_id, checker=None) -> bytes:
				while True:
					found = False
					for f in self.frames:
						if not checker or checker(f.data):
							found = True
							break

					if found:
						self.frames.remove(f)
						return f.data

		rp, _ = FoconFrame.unpack(bytes.fromhex('ff ff ff 01 49 2a 01 01 00 12 49 30 00 00 49 30 00 08 00 41 46 41 31 30 31 31 33 30 8c 03 ff ff'))
		rp.dest_id = args.source_id
		bus = FoconMessageBus(FoconMockBus(frames=[rp]), src_id=0)
		device = FoconDevice(bus, args.id)
		display = FoconDisplay(device)
		print(display.get_device_info())

		print(FoconDisplayInfo.unpack(
			bytes.fromhex('46 41 31 30 31 31 33 30') +
			b'foo'.ljust(0x1d-0x12, b'\x00') +
			str(42690).encode('ascii').ljust(0x28-0x1d, b'\x00') +
			b'abcde'.ljust(0x33-0x28, b'\x00') +
			b'lel'.ljust(0x44-0x33, b'\x00')
		))
	self_test_parser = debug_subcommands.add_parser('self-test')
	self_test_parser.set_defaults(_handler=do_self_test)

	args = p.parse_args()
	root_logger = logging.getLogger()
	root_logger.addHandler(logging.StreamHandler())
	root_logger.setLevel(logging.DEBUG if args.debug else logging.INFO)
	args._handler(args)
