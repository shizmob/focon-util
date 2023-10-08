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

A1 - Power GND
B1 - Power Vcc
B2 - NC
 3: Addr0
 4: Addr1
 5: Addr2
 6: Addr3
```

X2:
```
  /-------\
Y | 1 2 3 |
  |-------|
X | 1 2 3 |
  ---------

X1: RS485 IN-
X2: RS485 IN+
Y1: RS485 OUT-
Y2: RS485 OUT+
 3: GND
```

Connect a 60-140V DC power supply to pins B1 and A1, and bridge the address pin pairs as desired (or leave them all unbridged for ID 0).
Connect a RS485 transceiver to pins X1, X2, and X3, and a 120 ohm terminating resistor between Y1 and Y2.

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

## License

[WTFPL](./COPYING).
