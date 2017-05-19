# Music on Blocks
The Music on Blocks Project creats a nice wooden remote to control your sonos music system. 
The Project idea is heavely based on this project: https://github.com/shawnrk/songblocks and uses some stuff for the nfc reader from adafruit: https://learn.adafruit.com/adafruit-nfc-rfid-on-raspberry-pi?view=all
Furthermore the Project uses SoCo: https://github.com/SoCo/SoCo and Flask.


## Setting it all up

You'll need a raspberry pi with some linux on it. I always use a raspbian image, but it also should work on other images. 
After installing the raspbian, I recommend to change the default password and the hostname. 

### Scematics
The whole box consists of a raspbery pi with a couple of different components connected to it:

- a rfid reader 
    - connected over spi or uart
    - like RFID-RC522 (spi) or ...
- a rotary switch and two extra switches
- a led


### RFID Reader
I used the RFID-RC522 reader. It is very cheap an works, but the antenna is not very strong. 

To use it we have to enable SPI Interface in the rasperry pi settings:

```
sudo raspi-config
in "Advanced Options"  enable "SPI"

Installation SPI-Py (as root)

apt install python-dev
apt install gcc
git clone https://github.com/lthiery/SPI-Py
cd SPI-Py
python setup.py install

```

If you use the Adafruit PN532, you'll have to install nfcpy and have to blacklist the kernel driver:

```
echo "blacklist pn532" | sudo tee -a /etc/modprobe.d/blacklist-nfc.conf
```

### Install the LED stuff
The LED needs pigpio to correct fading. 
Pigpio: http://abyz.co.uk/rpi/pigpio/download.html

```
wget https://github.com/joan2937/pigpio/archive/master.zip
unzip master.zip
cd pigpio-master
make -j4
sudo make install
```


### Install Music on Blocks

Download the source: (perhaps you'll have to install git, python and python-pip)
```
git clone https://github.com/clemenstyp/music-on-blocks.git
```

change into the application folder
```
cd music-on-blocks
```
The Application depends on several external libraries. The easiest way to install everything is by running the following command (perhaps you'll have to run the command with sudo):

```
pip install -r requirements.txt --upgrade
```


Once all dependanices have been installed, rename `settings.py.example` to `settings.py` and edit the file.


## Basic Usage
Run `python startBlocks.py` to start the application. Then open up a web browser and visit [http://raspberryPi:8080](http://raspberryPi:8080).

You can also use the startScript.sh, or call it from /etc/rc.local 

## Todo:
im rotary habe ich bei mir den pull up auf ein pull down geändert (oder andersrum - daher funktioniert der rotery nicht richtig) - den rotary konfigurierbar machen, damit der auch beim johannes läuft. 


## License

Copyright (C) 2012 Clemens Putschli ([clemens@putschli.de](mailto:clemens@putschli.de) / [@clemenstyp](http://twitter.com/clemenstyp)).

Released under the [MIT license](http://www.opensource.org/licenses/mit-license.php).

