# RPiIoT
Assorted Python modules for Raspberry Pi automation / Internet of Things

Most of the Raspberry Pi Zero daughter boards that I've designed include a software controllable LED and tactile pushbutton, and many of them include a battery controller and charge circuit that can send a signal when the battery voltage has dropped below a level at which point the controller will generate a signal that can be used monitored by an RPi to cause it to shutdown. (The [AdaFruit PowerBoost 1000C](https://www.adafruit.com/product/2465) can do this. Remember to use a level shifter.)

Prime examples of this kind of board are [PowerBoard](http://github.com/jdimpson/PowerBoard) and [PowerHolder](http://github.com/jdimpson/PowerHolder) PCB projects. This code also works with [FitFullBoard](http://github.com/jdimpson/FitFullBoard), which doesn't have a battery but does send a shutdown signal to the RPi with the intention of it shutting down.

The contents of this repo are currently limited to the code required to driving the indication and battery monitoring  PCB projects listed above, but as I release more boards that do other things, I'll add to this collection.

* [powerboard.py](./powerboard.py) - Primarily used as a command-line tool that implements functionality to monitor button presses, controls LED, and monitor the low battery signal, entering grace period and shutting down as needed. Needs a little work before it can be used as a module. [See wiki entry for documentation](https://github.com/jdimpson/RPiIoT/wiki/powerboard.py).
* [multibutton.py](./multibutton.py) - Button class that lets you register callbacks for single clicks, double clicks, short clicks, and long clicks.
* [lbo.py](./lbo.py) - Threaded class that monitors a GPIO port. When the port is high, assume battery is OK. When port goes low, assumes that battery power level has gone too low. It will wait some grace period time before executing the shutdown command. If the port goes high again during the grace period, the shutdown countdown is cancelled. If when the code is first run the port is not high, the monitor thread will exit, assuming the unit is not being run off of a battery.
* [netinfo.py](./netinfo.py) - Various utility functions to check network configuration and state.
* [netctrl.py](./netctrl.py) - Various utility functions to change network configuration and state.
* [wall.py](./wall.py) - A class that wraps around the classic Unix "wall" command, including an option to pop-up a message in an X-WIndows environment.
* [kvgetopts.py](./kvgetopts.py) - My own version of getopts, which parses argv full of "key=value" command line arguments.

Mosto of these require the gpiozero python library. They are currently python 2, so you definitely shouldn't use them. Most of these libraries can be executed directly on the command line, either being useful on their own, or serving as test / example code for using the library.
