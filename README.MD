# RTD-2660-Programmer(for)Python

This is a python port of [ghent360](https://forums.adafruit.com/viewtopic.php?f=47&t=84068)'s [RTD-2660-Programmer](https://github.com/ghent360/RTD-2660-Programmer) utilizing the Adafruit FT232H for i2c communication with your Realtek RTD2660-based lcd controller. If this project helps you out, send your beers to [ghent360] first, he/she did all the heavy lifting.

### Notes - General:
  - This was done quick and very dirty
  - Writing to the flash is not currently supported. The c methods ProgramFlash and ReadFile are copied into my source, but commented out and not yet translated to python.
  - I've never touched python before this so I'm sure some things are very wrong from a style perspective
  - I used python 2.7.11
  - I may not ever update this as I've already got what I needed out of the project, which was to read out the firmware from one of my controllers and then clone it to another board with [this tool](http://tech.mattmillman.com/lcd/rovatools/) from [matt millman](http://tech.mattmillman.com/) (his rovatool, didn't support dumping firmware at the time).


### Notes - Reading firmware
- Reading is painfully slow, taking upwards of 9 mins for a 512 Kb dump. The faster Adafruit GPIO method ``readList`` kept failing for me with ACK errors, so I had to fall back to reading a single byte at a time.
- The firmware images compatible with my LCDs are 256K, but the flash is (supposedly) 512K so my test dumps yielded extra stuff. I'm not sure whether this data is relevant at all (runtime variables maybe) or what rules I need to follow for ending the read operation earlier. Just keep in mind that you might pull more info than needed and will likely have to truncate it manually. 


### Setup
- Get Python, the libusbK driver, and Adafruit's Python GPIO library installed by following Adafruit's FT232H breakout tutorial [https://learn.adafruit.com/adafruit-ft232h-breakout/overview]
- Wire up your FT232 to the controller's VGA port using this schematic [http://tech.mattmillman.com/lcd/rovatools/ftdi-ft232h/]. (I didn't tie all the ground pins together as recommended by the diagram. It communicated just fine for me with a single jumper wire plugged into VGA pin 6 for ground. YMMV)

### Usage
```sh
$ python prog.py -h
usage: Adafruit_I2C_test.py [-h] [--flash-filename FLASHFILE]
                            [--dump-filename READFILE]

RTD2660 Flash Reader.

optional arguments:
  -h, --help            show this help message and exit
  --flash-filename FLASHFILE
                        Flash this file to the controller
  --dump-filename READFILE
                        Read into this file from the controller
```

> dump firmware
```sh
$ python prog.py --dump-filename path/to/save/file.bin
```

> load firmware (method commented out and untested, in all likelyhood, it's broken)
````sh
$ python prog.py --flash-filename path/to/load/file.bin
````
