import RPi.GPIO as gpio
import time

gpio.setmode(gpio.BCM)
gpio.setup(17, gpio.OUT)

gpio.output(17, gpio.HIGH)
time.sleep(5)
gpio.output(17, gpio.LOW)

gpio.cleanup()
