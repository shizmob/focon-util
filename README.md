# `focon-util`

Utility and library to talk to industrial devices from Focon Electronics Systems A/S, as used in:
* Stadsgewestelijk Materieel-gemoderniseerd (SGMm) operated by the Dutch railway company Nationale Spoorwegen (NS);
* Various trains operated by the Danish railway company Danske Statsbaner (DSB);

## Installation

* Use pip: `pip install .`

## Usage

### Displays

Supported displays will have two connectors on the side, labeled `X1` and `X2`, with the following pin-out:

X1:
```
  /-------------------\
A | 1  -  3  4  5  6  |
B | 1  2  3  4  5  6  |
  ---------------------

A1: power GND
B1: power Vcc
B2: N/C
 3: address bit 0
 4: address bit 1
 5: address bit 2
 6: address bit 3
```

X2:
```
  /-------\
Y | 1 2 3 |
  |-------|
X | 1 2 3 |
  ---------

X1: RS-485 in-
X2: RS-485 in+
Y1: RS-485 out-
Y2: RS-485 out+
 3: RS-485 GND
```

Connect a 60-140V DC power supply to pins B1 and A1, and bridge the address pin pairs as desired (or leave them all unbridged for ID 0).
Connect a RS-485 transceiver to pins X1, X2, and X3, and a 120 ohm terminating resistor between Y1 and Y2.

Now, use any of the display subcommands to talk to the device, passing the path to your serial device using `-d` and the device address using `-i`:

```
$ focon-util -d /dev/ttyUSB0 -i 0 display info
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

If this does not work, check your address pins and RS-485 connectivity. To make sure your display works at all, try bridging all adress pin pairs: upon startup, the display should then enter self-test mode.

## License

[WTFPL](./COPYING).
