# Hatchling - brooding chicken eggs the fancy way

This DIY project simply started off with wanting to learn python and basic hardware control with a raspberry pie and developed into a full blown chicken egg incubator. The idea was to build the controller as much as possible from scratch with cheap, but reliable parts. The python code should move the eggs periodically and control the temperature via a PID controller, report temperature, humidity and current duty cycle. On top, the controller should visually show the correct values via LEDs and warn, if there are problems arising. 

<img align="right" src="chicken_control.png" width = 320 hight = 240>

Features:
* works on any raspberry pie & possibly other controllers
* uses cheap off the shelve or recycled parts
* PID controlled temperature
* simple status reporting of correct temperature & humidity via LEDs
* accustic warning, when values are far off the set points
* automatic turning of eggs
* easy to use via CLI
* includes incubation programs for other species (e.g.: ducks, quails, ...)
* runs savely for days without burning down the house...
* reports current values via dash

WIKI IS STILL UNDER CONSTRUCTION  
Find all the detailed info [here](https://github.com/mstemmer/hatchling/wiki)

## Usage

run `python hatchling.py`
```
usage: hatchling [-h] [-i] [-s]

optional arguments:
  -h, --help       show this help message and exit
  -i, --init       Start new incubation. Default: resume last incubation
                   program
  -s , --species   Load species specific incubation program: chicken, quail,
                   elephant
```
