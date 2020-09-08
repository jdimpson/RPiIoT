# RPiIoT
Assorted Python modules for Raspberry Pi automation / Internet of Things

Most of the Raspberry Pi Zero daughter boards that I've designed include a software controllable LED and tactile pushbutton, and many of them include a battery controller and charge circuit that can send a signal when the battery voltage has dropped below a level at which point the controller will generate a signal that can be used monitored by an RPi to cause it to shutdown.

Prime examples of this kind of board are [PowerBoard](http://github.com/jdimpson/PowerBoard) and [PowerHolder](http://github.com/jdimpson/PowerHolder).

Given this hardware baseline, I wrote the first version of code that became powerboard.py, that roughly implemented the following functionality:
> When running from boot, pulse until wifi gets link

>                      then off after wifi gets link
> When button is short pressed, toggle solid LED on/off
> When button is long pressed (>=5 sec), flash until by poweroff
> When low battery is asserted, flash for 60 secs, continue flash until poweroff
> Poweroff overrules low battery overrules short button overrules wifi state
>

THe WiFi flash functionality is currently commented out because it annoyed me, and added a grace period which will stop the shutdown countdown if external power is acquired.

* [powerboard.py](./powerboard.py) - Primarily used as a command-line tool that implements the algorithm described above.
* [multibutton.py](./multibutton.py) - Button class that lets you register callbacks for single clicks, double clicks, short clicks, and long clicks.
* [lbo.py](./lbo.py) - Threaded class that monitors a GPIO port. When the port is high, assume battery is OK. When port goes low, assumes that battery power level has gone too low. It will wait some grace period time before executing the shutdown command. If the port goes high again during the grace period, the shutdown countdown is cancelled. If when the code is first run the port is not high, the monitor thread will exit, assuming the unit is not being run off of a battery.
* [netinfo.py](./netinfo.py) - Various utility functions to check network configuration and state.
* [netctrl.py](./netctrl.py) - Various utility functions to change network configuration and state.
* [wall.py](./wall.py) - A class that wraps around the classic Unix "wall" command, including an option to pop-up a message in an X-WIndows environment.
* [kvgetopts.py](./kvgetopts.py) - My own version of getopts, which parses argv full of "key=value" command line arguments.

Mosto of these require the gpiozero python library. They are currently python 2, so you definitely shouldn't use them. Most of these libraries can be executed directly on the command line, either being useful on their own, or serving as test / example code for using the library.
