# NS SGMm displays

These comprise at least the following devices:
- Focon 800222-01 ("INTERNAL DISPLAY SGMIII"): default configuration for reference in `ns-sgmiii.id.config.bin`
- Focon 800224-01 ("EXTERNAL DISPLAY SGMIII"): default configuration for reference in `ns-sgmiii.ed.config.bin`

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

Connect a 60-140V DC power supply to pins B1 and A1, and bridge the address pin pairs as desired (or leave them all unbridged for ID 0).

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

Connect a RS-485 transceiver to pins X1, X2, and X3.
Connect Y1, Y2, and Y3 through to X1, X2, and X3 of the next device if you're setting up a daisy chain,
or put a 120 ohm termination resistor between Y1 and Y2 if this is the last device.

Testing so far indicates it also works without this termination resistor at reasonable distances.

## Firmware modifications

### Baudrate increase

The firmware programs a clock divisor in the communication chip (UART transceiver) to obtain the standard 57.6 kbaud/s communication speed.
By tweaking this divisor, it's possible to bump the communication speed, and thus the maximum framerate, to 115.2 kbaud/s.

A [binary patch for application version 1.30](ns-sgmiii.app.130-baud115k.xd3) is available. Given the application extracted from a flash dump (using `focon-util flash unpack`), it can be applied using `xdelta3`:

```sh
xdelta3 -d -s ns-sgmiii.app.130.bin ns-sgmiii.app.130-baud115k.xd3 ns-sgmiii.app.130-baud115k.bin
```

The modified application can then be flashed through `focon-util`:

```sh
focon-util display selfdestruct                       # erase existing application
focon-util info                                       # ensure the device is now in bootloader mode
focon-util boot flash ns-sgmiii.app.130-baud115k.bin  # flash new application
focon-util boot launch                                # boot into new application
focon-util -b 115200 info                             # ensure the device is in application mode and responding at 115.2 kbaud/s
```

Once successful, the `-b <BAUDRATE>` argument can be used (*before any subcommand*) to communicate with the device.
Note that if the device is in bootloader mode, it will still use the original 57.6 kbaud/s speed.
