

idea is based on this:

https://github.com/shawnrk/songblocks

pn 532:

https://learn.adafruit.com/adafruit-nfc-rfid-on-raspberry-pi?view=all




# music-on-blocks

von: http://raspmer.blogspot.de/2015/07/how-to-use-rfid-rc522-on-raspbian.html

Before use RFID-RC522. Enable SPI Interface (Device Tree Overlays)

On new kernel use Device Tree Overlays.

Edit on /boot/config.txt and add the following:

device_tree_param=spi=on
dtoverlay=spi-bcm2708

And edit /etc/modprobe.d/raspi-blacklist.conf and add # (comment) on line "blacklist spi-bcm2708"

it should look like this one: #blacklist spi-bcm2708

After a reboot Raspberry PI (sudo shutdown -r now) you can re-check SPI Interface software by calling: 
`$ dmesg | grep spi`
`[    5.408904] bcm2708_spi 20204000.spi: master is unqueued, this is deprecated`
`[    5.659213] bcm2708_spi 20204000.spi: SPI Controller at 0x20204000 (irq 80)`

`$ lsmod`
`spi_bcm2708             6010  0`

Reference : https://github.com/raspberrypi/firmware/tree/master/boot/overlays


Edit on /etc/modprobe.d/raspi-blacklist.conf

add # (comment) on line "blacklist spi-bcm2708"

#blacklist spi-bcm2708

Reboot Raspberry PI

sudo shutdown -r now

Re-Check SPI Interface software

$ dmesg | grep spi
[    5.408904] bcm2708_spi 20204000.spi: master is unqueued, this is deprecated
[    5.659213] bcm2708_spi 20204000.spi: SPI Controller at 0x20204000 (irq 80)

$ lsmod
spi_bcm2708             6010  0

If you found, software is enabled.

Install Software for use RFID-RC522
Install python-dev

sudo apt-get install python-dev

Install SPI-Py (Hardware SPI as a C Extension for Python)

git clone https://github.com/lthiery/SPI-Py.git
cd SPI-Py
sudo python setup.py install

Install MFRC522-python

git clone https://github.com/mxgxw/MFRC522-python.git
cd MFRC522-python



Install Pins between Raspberry PI and RFID-RC522

RFID-RC522 Pin
 Raspberry PI Pin
Raspberry PI Pin name
SDA
  24
    GPIO8
SCK
  23
    GPIO11
MOSI
  19
    GPIO10
MISO
  21
    GPIO9
IRQ
  None
    None
GND
  Any
    Any Ground
RST
  22
    GPIO25
3.3V
  1
    3V3

You can test read card.
sudo python Read.py
Welcome to the MFRC522 data read example
Press Ctrl-C to stop.
If touch the card, it will display.

Welcome to the MFRC522 data read example
Press Ctrl-C to stop.
Card detected
Card read UID: XX,XX,XX,XX
Size: 8
Sector 8 [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
Ctrl+C for Stop.

And test write card.

$ sudo python Write.py
Card detected
Card read UID: XX,XX,XX,XX
Size: 8

Sector 8 looked like this:
Sector 8 [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

Sector 8 will now be filled with 0xFF:
4 backdata &0x0F == 0x0A 10
Data written

It now looks like this:
Sector 8 [255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255]

Now we fill it with 0x00:
4 backdata &0x0F == 0x0A 10
Data written

It is now empty:
Sector 8 [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

You can learning python code for use RFID read and write data.

MIFARE (MFRC522) datasheet : http://www.nxp.com/documents/data_sheet/MFRC522.pdf


and other python library : https://github.com/ondryaso/pi-rc522