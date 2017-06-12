#!/bin/sh
sudo pigpiod
cd "$(dirname "$0")"
while true; do
	sudo python startBlocks.py
    for i in {1..5};do
        sleep 1
        printf "wait"
    done
    printf "\n"
done
