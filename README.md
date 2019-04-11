# TiCo

TiCo, initially started as TeachIn, is an app for the [ftc firmware](https://cfw.ftcommunity.de/ftcommunity-TXT/de/) to control a 4 axes teach-in robot. Control HW consists of a [TX-Pi](https://github.com/ftCommunity/tx-pi) to run the community firmware, a [ftDuino](https://www.ftduino.de) to provide I/Os and I2C, two [ft-adapted Adafruit v2 motor shields](https://www.thingiverse.com/thing:3431659), connected via I2C to the ftDuino, to hook up the three stepper motors for axes 1-3 and finally an [I2C mini servo shield](https://github.com/harbaum/ftduino/tree/master/addons/i2c-servo) for axis 4, the gripper, based on [Jan's great ft compatible servo system](https://www.thingiverse.com/thing:2807112).
The whole system (except the TX-Pi) is powered via a laptop power adapter and a step-down converter in a [3D printed case](https://www.thingiverse.com/thing:3477528) to provide 10.4 volts to the steppers. ftDuino and servo shield are 10.4V safe. 

The ftDuino runs a derivate of [ftduino_direct](https://cfw.ftcommunity.de/ftcommunity-TXT/de/) enhanced with some direct commands to address the motor shields and servo shield.

Currently TiCo provides a GUI to directly teach-in a list of position coordinates for the robot. This list can be run-through afterwards, so it provides just a simple point-to-point control of the robot.

Also the list can be stored and re-loaded into the app.

To do:
- limitation of the axes according to the pyhsical range of the robot
