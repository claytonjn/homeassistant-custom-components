# Home Assistant Custom Components
All my custom components for Home Assistant are in this repository.

## Custom Haiku with SenseME fan and light
The Haiku with SenseME fan is a WiFi connected fan and installable light. This custom component uses TomFaulkner's [SenseMe](https://github.com/TomFaulkner/SenseMe) library to communicate with the fan.

### Installation
There are three senseme.py files that must be installed in the config/custom_components directory. Note the location of the three senseme.py files in their respective folders (fan/ and light/) is important. The SenseMe library will be automatically installed by Home Assistant.

### Configuration
The Haiku with SenseME fan component will automatically discover and create a fan and light (if installed) for each discovered fan. Setting ```max_number_fans``` to the number of Haiku fans on your network will speed up the discovery process but is not required. If ```include:``` is specified, discovered fans with a matching name will be added. If ```exclude``` is specified, discovered fans with a matching name will NOT be added. If both ```include:``` and ```exclude``` are specified, only ```include:``` will be honored. If neither ```include:``` and ```exclude``` are specified, all auto-detected fans will be added.

For included fans you can now specify a ```friendly_name``` to use instead of ```name``` in Home Assistant. This is handy for grouped fans. Controlling any fan in a group will affect all fans of that group. Default value is the same as ```name ```. Also new in the include section is the ```has_light``` boolean which when ```true``` will add a light component along with the fan. The default for ```has_light``` is ```true```. The included fan section must have a ```name ``` variable and it must must match the name in the Haiku app.
```yaml
# enable Haiku with SenseMe ceiling fans
senseme:
  max_number_fans: 2
  # used to include only specific fans
  include:
    - name: "Studio Vault Fan"
      friendly_name: "Studio Fan"
      has_light: true
    - name: "Family Room Fan"
  # or use exclude to prevent specific auto-detected fan
  exclude:
    - "Studio Beam Fan"
```

### Problems
* Occasionally changes to the fan state fail to connect to fan and make the change, usually as a network (python socket) error. Same thing is true for the SenseMe background task which gets the complete fan state every minute.
* Originally the Senseme custom component auto-detected both the existence of a light and the fan's group but longer term usage showed a problem with consistently auto-detecting these values. This version no longer auto-detects these values and requires the user to specify them in advance.

## Custom MQTT Sharing component
In my Home Automation setup I use lots of SmartHome [Insteon](https://www.smarthome.com/insteon.html) devices controlled through an ISY-994i. This worked fine until I added another building to my property. Insteon devices support both RF and power line communication and neither worked consistently between the two buildings. I was also starting to add Z-Wave devices to my Home Automation system and it has the same problem between the two buildings. My solution was two instances of Home Assistant each with a Z-Stick for Z-Wave and an ISY-994i in each building. Now all my intra-building issues were solved but my attempts at using [MQTT Eventstream](https://www.home-assistant.io/components/mqtt_eventstream/) or [MQTT Statestream](https://www.home-assistant.io/components/mqtt_statestream/) to share data between multiple instances of Home Assistant left me wanting a solution that was a combination of both. With MQTT Eventstream events were shared (all mind you!) but entities were transient. If you restart Home Assistant all shared entities disappear until an event recreates the entity. With MQTT Statestream entity states are shared and retained but they are effectively read-only. What I really want is to share specified entities between two instances of Home Assistant where either instance can say turn a switch on and get state updates and receive events.

More information to come...
