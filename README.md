# `focon-util`

Utility and library to talk to industrial devices from Focon Electronics Systems A/S, as used in:
* Various trains operated by the Dutch railway company Nederlandse Spoorwegen (NS):
  * Stadsgewestelijk Materieel (gemoderniseerd) [SGMm, also known as Plan Y]
  * Intercitymaterieel (gemoderniseerd) [ICMm, also known as Plan Z]
* Various trains operated by the Danish railway company Danske Statsbaner (DSB)

## Installation

* Use pip: `pip install .`

## Usage

### Displays

For supported displays, refer to the `docs/` folder for hardware set-up:
- [NS SGMIII/SGMm internal and external display](docs/ns-sgmiii.md)
- [NS ICMm external display](docs/ns-icmm.md)

The `display` subcommand can then be used to talk to the device. If your RS-485 transceiver is not at `/dev/ttyUSB0`, you can specify its path using `-d`. If the display is not at address 0, you can specify its address using `-i`:

```
$ focon-util -d /dev/ttyUSB3 -i 2 display info
boot:
  type:    FA
  version: 1.01

app:
  version: 1.30

product:
  part:    390024
  name:    Focon Electronics Systems A/S DSB dot 16

stats:
  memory:  FreeBuffer: 8:20:4 [S:M:L]  RunTime: 0:0:1:18 [D:H:M:S]
  network: SnpInfo Tx=000002, Rx=000003 --- Error: Pkt=00, PktNo=00, TxBuf=04, NoAnswer=00, Chk=00
  sensors: 19; EnvermentBrightness følger: %d mV

```

If the info command does not work, check your address pins and RS-485 connectivity. To make sure your display works at all, try bridging all adress pin pairs: upon startup, the display should then enter self-test mode.

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
