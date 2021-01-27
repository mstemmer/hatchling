# Hatchling - brooding chicken eggs the fancy way

This DIY project started off with wanting to experiment with python and basic hardware control with a RaspberryPi and developed into a full blown chicken egg incubator. The idea was to build the controller as much as possible from scratch with cheap, but reliable parts. The python code should move the eggs periodically and control the temperature via a PID controller, report temperature, humidity and current duty cycle. On top, the controller should visually show the correct values via LEDs and warn acoustically, if there are problems arising. 

<img align="right" src="https://github.com/mstemmer/hatchling/blob/main/docs/chicken_control.png" width = 320 hight = 240>

Features:
* works on any RaspberryPi & possibly other controllers
* uses cheap off the shelf or recycled parts
* PID controlled temperature
* simple status reporting of correct temperature & humidity via LEDs
* acoustic warning, when values are far off the set points
* automatic turning of eggs
* easy to use via CLI
* flexible incubation programs for other species (e.g.: ducks, quails, ...)
* creates log and data files
* reports current values via plotly dash

Find all the details about the hardware & software in the [Wiki](https://github.com/mstemmer/hatchling/wiki)!

## Quick start
- make sure you run python3 (>=3.7)
- will ony work, when RaspberryPi is configured and connected to the controller
- Please see [Configuration](https://github.com/mstemmer/hatchling/wiki/Configuration) and the [Wiki](https://github.com/mstemmer/hatchling/wiki) in general

```
python -m venv hatch_env
source hatch_env/bin/activate
pip install -r requirements.txt
```

Run hatchling with:  
`python hatchling.py`
```
usage: hatchling [-h] [--init] [--species] [--silent] [--fixed_dc]

optional arguments:
  -h, --help   show this help message and exit
  --init       Start new incubation. Default: resume from last time point
  --species    Load species specific incubation program: chicken, quail,
               elephant. See inc_program.json
  --silent     Deactivate the alarm buzzer
  --fixed_dc   Ignores PID controller and sets heater to fixed duty cycle.
```
## Run the data monitoring server (Optional)
<img align="right" src="https://github.com/mstemmer/hatchling/blob/main/docs/images/dash_4.png" width = 640 hight = 480>
Hatchling reports its status via the command line and the LED/buzzer on the controller. With dash you can extend the monitoring to all your end devices within your network.
 
<br/><br/><br/><br/>
Run the dash server with:  
`python monitor.py --input <data-folder/data-file.csv>`
The server is set up to run as local host. So in order to access the page, type the IP of your RaspberryPi in your browser of your end device and use port 8050 (e.g.: 192.169.168:8050). See more info under the [Software](./Software) section.

## Note 
So far this has been running smoothly for me. Make sure though that everything is solderd and insulated correctly. Dont run hatchling when you are away! Keep an eye on the heating element!
