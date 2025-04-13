# `focon-util`

Utility and library to talk to industrial devices from Focon Electronics Systems A/S, as used in:
* Various trains operated by the Dutch railway company Nederlandse Spoorwegen (NS):
  * Stadsgewestelijk Materieel (gemoderniseerd) [SGMm, also known as Plan Y]
  * Intercitymaterieel (gemoderniseerd) [ICMm, also known as Plan Z]
* Various trains operated by the Danish railway company Danske Statsbaner (DSB)

## Installation

* Use pip: `pip install .`

## Usage

Supported devices communicate over RS-485: a transceiver is required, `focon-util` assumes by default that it is present at `/dev/ttyUSB0`.
For transceivers at a different path, the `-d <path>` argument (*before any subcommand*) can be used.

As the RS-485 bus Focon uses is multi-drop, devices have an *address*, typically configured by bridging physical pins on their connectors.
`focon-util` assumes by default that the device you are talking to is at address 0 (all pins unbridged).
For devices at a different address, the `-i ADDRESS` argument (*before any subcommand*) can be used.

Finally, the system `focon-util` is running at also needs an address to be able to talk on the bus: by default, `focon-util` will use address 14. If there is already a device at address 14, the `-s ADDRESS` argument (*before any subcommand*) can be used to specify a different address.

Once your device is wired up (see the specific sub-sections below), you can use subcommands to communicate with them.
The `info` subcommand works for all devices, and should show an output like such:

```
$ focon-util -d /dev/ttyUSB3 -i 2 info
boot:
  mode:    Application
  type:    F
  version: 1.01

app:
  version: 1.30
```

If the info command does not work, check your address pins and RS-485 connectivity.

### Displays

For supported displays, refer to the `docs/` folder for hardware set-up:
- [NS SGMIII/SGMm internal and external display](docs/ns-sgmiii.md)
- [NS ICMm external display](docs/ns-icmm.md)

If you want to verfify your display works at all, try bridging all adress pin pairs: upon startup, the display should then enter self-test mode.

Once connected, the `display` subcommand can be used to talk to the device. The `display` subcommand itself has a number of subcommands to control various functions of the device. For example, the `info -a` display subcommand will show all display-specific information:

```
$ focon-util display info -a
boot:
  mode:    Application
  type:    F
  version: 1.01

app:
  version: 1.30

display:
  part:    300338

assets:
  part:    390024
  name:    Focon Electronics Systems A/S DSB dot 16
  version: 1.01
  size:    [...]
  fonts:   1

stats:
  memory:  FreeBuffer: 8:20:4 [S:M:L]  RunTime: 0:0:1:18 [D:H:M:S]
  network: SnpInfo Tx=000002, Rx=000003 --- Error: Pkt=00, PktNo=00, TxBuf=04, NoAnswer=00, Chk=00
  sensors: 19; EnvermentBrightness følger: %d mV

tasks:
  [...]
```

Currently supported display commands are:
* Informational:
  - Show extended information: `focon-util display info`
  - Show display configuration: `focon-util display config`
  - Show display status: `focon-util display status`
  - Enter or leave one of the self-test modes:
    - Diagnostic information: `focon-util display selftest info`
    - Pixel flood: `focon-util display selftest flood`
  - Leave self-test mode: `focon-util display selftest abort`
* Drawing:
  - Draw text object: `focon-util display print "Beste reizigers"`
  - Draw image object: `focon-util display draw frostedbutts.png`
  - Draw filled rectangle: `focon-util display fill [...]`
  - Hide area: `focon-util display hide [...]`
  - Change properties of drawn object: `focon-util display redraw [...]`
  - Remove drawn object(s): `focon-util display undraw [...]`

## License

[WTFPL](./COPYING).
