# Music on Blocks

The Project is bases on the SoCo: https://github.com/SoCo/SoCo and Flask

The Idea is based on this project: https://github.com/shawnrk/songblocks and uses some stuff for the nfc reader from adafruit: https://learn.adafruit.com/adafruit-nfc-rfid-on-raspberry-pi?view=all


## Set up

You'll need a raspberry pi with some linus on it. I always use a raspbian image, but it also should work on other images. 

After installing the raspbian, I recommend to change the default password and the hostname. 

Before we can use RFID-RC522 we have to enable SPI Interface 

`sudo raspi-config`
in "Advanced Options"  enable "SPI"

Installation SPI-Py (as root)

apt install python-dev
apt install gcc
git clone https://github.com/lthiery/SPI-Py
cd SPI-Py
python setup.py install




Download the source: (perhaps you'll have to install git, python and python-pip)
`git clone https://github.com/clemenstyp/music-on-blocks.git`

change into the application folder
`cd music-on-blocks`

The Aplication depends on several external libraries. The easiest way to install everything is by running the following command:

`pip install -r requirements.txt --upgrade`

oder mit sudo

But for the led you'll have to install pigpio: http://abyz.co.uk/rpi/pigpio/download.html

rm master.zip
sudo rm -rf pigpio-master
wget https://github.com/joan2937/pigpio/archive/master.zip
unzip master.zip
cd pigpio-master
make -j4
sudo make install

Once all dependanices have been installed, rename `settings.py.example` to `settings.py` and edit the file.

## Basic Usage
Run `python startBlocks.py` to start the application. Then open up a web browser and visit [http://raspberryPi:8080](http://raspberryPi:8080).

You can also use the startScript.sh, or call it from /etc/rc.local 

##todo:
im rotary habe ich bei mir den pull up auf ein pull down geändert (oder andersrum - daher funktioniert der rotery nicht richtig) - den rotary konfigurierbar machen, damit der auch beim johannes läuft. 


## License

Copyright (C) 2012 Clemens Putschli ([clemens@putschli.de](mailto:clemens@putschli.de) / [@clemenstyp](http://twitter.com/clemenstyp)).

Released under the [MIT license](http://www.opensource.org/licenses/mit-license.php).

