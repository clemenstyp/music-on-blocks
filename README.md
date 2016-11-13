# Music on Blocks

The Project is bases on the SoCo: https://github.com/SoCo/SoCo and Flask

The Idea is based on this project: https://github.com/shawnrk/songblocks and uses some stuff for the nfc reader from adafruit: https://learn.adafruit.com/adafruit-nfc-rfid-on-raspberry-pi?view=all


## Set up

You'll need a raspberry pi with some linus on it. I always use a raspbian image, but it also should work on other images. 

After installing the raspbian, I recommend to change the default password and the hostname. 

Before we can use RFID-RC522 we have to enable SPI Interface (Device Tree Overlays) (http://raspmer.blogspot.de/2015/07/how-to-use-rfid-rc522-on-raspbian.html)

Edit on /boot/config.txt and add the following:

device_tree_param=spi=on
dtoverlay=spi-bcm2708

And edit /etc/modprobe.d/raspi-blacklist.conf and add # (comment) on line "blacklist spi-bcm2708"

it should look like this one: #blacklist spi-bcm2708

After a reboot Raspberry PI (sudo shutdown -r now) you can re-check SPI Interface software by calling: 
$ dmesg | grep spi
[    5.408904] bcm2708_spi 20204000.spi: master is unqueued, this is deprecated
[    5.659213] bcm2708_spi 20204000.spi: SPI Controller at 0x20204000 (irq 80)

$ lsmod
spi_bcm2708             6010  0


The Aplication depends on several external libraries. The easiest way to install everything is by running the following command:

`pip install -r requirements.txt`

Once all dependanices have been installed, rename `settings.py.example` to `settings.py` and edit the file.

## Basic Usage
Run `python startBlocks.py` to start the application. Then open up a web browser and visit [http://raspberryPi:8080](http://raspberryPi:8080).

## License

Copyright (C) 2012 Clemens Putschli ([clemens@putschli.de](mailto:clemens@putschli.de) / [@clemenstyp](http://twitter.com/clemenstyp)).

Released under the [MIT license](http://www.opensource.org/licenses/mit-license.php).

