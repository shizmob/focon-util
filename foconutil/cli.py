import argparse
import logging

from . import FoconFrame, FoconSerialTransport, FoconBus, FoconMessageBus, FoconDisplay
from .devices.display import *


def main() -> None:
        p = argparse.ArgumentParser()
        p.add_argument('-d', '--device', default='/dev/ttyUSB0', help='bus device')
        p.add_argument('--no-flow-control', action='store_false', dest='flow_control', default=True, help='disable hardware flow control')
        p.add_argument('-D', '--debug', action='store_true', help='debug log')
        p.add_argument('-s', '--source-id', type=int, default=14, help='source device ID')
        p.add_argument('-i', '--id', type=int, default=0, help='device ID')
        p.set_defaults(_handler=None)

        subcommands = p.add_subparsers(title='subcommands', required=True)


        # General subcommands

        def do_info(args):
                bus = FoconMessageBus(FoconBus(FoconSerialTransport(args.device, flow_control=args.flow_control), args.source_id), args.source_id)
                device = FoconDevice(bus, args.id)
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

        # Display subcommands

        def do_display(args):
                bus = FoconMessageBus(FoconBus(FoconSerialTransport(args.device), args.source_id), args.source_id)
                device = FoconDevice(bus, args.id)
                display = FoconDisplay(device)

                args._display_handler(display, args)
        display_parser = subcommands.add_parser('display')
        display_parser.set_defaults(_handler=do_display, _display_handler=None)
        display_subcommands = display_parser.add_subparsers(title='display subcommands', required=True)

        def do_display_info(display, args):
                device_info = display.get_device_info()
                print('boot:')
                print('  type:   ', device_info.kind)
                print('  version: {}.{:02}'.format(*device_info.boot_version))
                print()

                print('app:')
                print('  version: {}.{:02}'.format(*device_info.app_version))
                print()

                print('product:')
                product_info = display.get_product_info()
                print('  part:   ', product_info.num)
                print('  name:   ', product_info.name)
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

        def do_display_get_boot_info(display, args):
                print(display.get_boot_info())
        get_boot_info_parser = display_subcommands.add_parser('boot-info')
        get_boot_info_parser.set_defaults(_display_handler=do_display_get_boot_info)

        def do_display_get_ext_info(display, args):
                print(display.get_ext_info())
        get_ext_info_parser = display_subcommands.add_parser('ext-info')
        get_ext_info_parser.set_defaults(_display_handler=do_display_get_ext_info)

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

        def do_display_status(display, args):
                print(display.get_status())
        get_status_parser = display_subcommands.add_parser('status')
        get_status_parser.set_defaults(_display_handler=do_display_status)

        def do_display_product_info(display, args):
                print(display.get_product_info())
        get_product_info_parser = display_subcommands.add_parser('product-info')
        get_product_info_parser.set_defaults(_display_handler=do_display_product_info)

        def do_display_test_disp_304(display, args):
                print(display.test_disp_304())
        test_disp_304_parser = display_subcommands.add_parser('test-disp-304')
        test_disp_304_parser.set_defaults(_display_handler=do_display_test_disp_304)

        # Display drawing commands

        def do_display_draw(display, args):
                # Obtain (and store) config if needed
                config = None
                config_bytes = args.config.read() if args.config else None
                if config_bytes:
                        try:
                                config = FoconDisplayConfiguration.unpack(config_bytes)
                        except:
                                print('display configuration was corrupted, re-reading')
                                config_bytes = None
                if not config:
                        config = display.get_current_config()
                        if args.config:
                                args.config.truncate(0)
                                args.config.write(config.pack())
                display.use_config(config)
                return args._display_draw_handler(display, args)

        def add_display_draw_args(parser):
                parser.add_argument('-c', '--config', type=argparse.FileType('a+b'), help='path to file containing display configuration to use (will be written if specified but empty or invalid)')
                parser.add_argument('-C', '--composition', type=FoconDisplayDrawComposition.parse, choices=list(COMPOSITION_NAMES))
                parser.add_argument('-f', '--effect', type=FoconDisplayObjectEffect.parse, choices=list(EFFECT_NAMES))
                parser.set_defaults(_display_handler=do_display_draw, _display_draw_handler=None)

        def do_display_print(display, args):
                print(display.print(args.message, effect=args.effect))

        print_parser = display_subcommands.add_parser('print')
        add_display_draw_args(print_parser)
        print_parser.set_defaults(_display_draw_handler=do_display_print)
        print_parser.add_argument('message')

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

                        def recv_message(self, checker=None) -> bytes:
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
