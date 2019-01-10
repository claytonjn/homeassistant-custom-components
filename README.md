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

## Custom MQTT Sharing components
In my Home Automation setup I use lots of SmartHome [Insteon](https://www.smarthome.com/insteon.html) devices controlled through an ISY-994i. This worked fine until I added another building to my property. Insteon devices support both RF and power line communication and neither worked consistently between the two buildings. I was also starting to add Z-Wave devices to my Home Automation system and it has the same problem between the two buildings. My solution was two instances of Home Assistant each with a Z-Stick for Z-Wave and an ISY-994i in each building. Now all my intra-building issues were solved but my attempts at using [MQTT Eventstream](https://www.home-assistant.io/components/mqtt_eventstream/) or [MQTT Statestream](https://www.home-assistant.io/components/mqtt_statestream/) to share data between multiple instances of Home Assistant left me wanting a solution that was a combination of both. With MQTT Eventstream events were shared (all mind you!) but entities were transient. If you restart Home Assistant all shared entities disappear until an event recreates the entity. With MQTT Statestream entity states are shared and retained but they are effectively read-only. What I really want is to share specified entities between two instances of Home Assistant where either instance can say turn a switch on and get state updates and receive events.

The custom components are mqtt_sharehost and mqtt_shareclient. The host Home Assistant instance is the one that already has the entities you want to share. Thus the client Home Assistant instance is one the entities are shared with. As shown in the diagram below the mqtt_sharehost is on right side and it is sharing three enities. Each entity has it's own state topic on the MQTT server and they are published with the retain flag. This prevents the shared entities from disappearing after a restart. If any of the entities are ISY994 devices then "isy994_control" events are published to the event topic. On the left side the mqtt_shareclient is listening to all state topic using topic wildcards and isy994_controls event from the mqtt_sharehost. The host also publishes control "call_service" events back to the mqtt_sharehost using the control topic. Any number of mqtt_shareclient's can listen to a single mqtt_sharehost. It is also important that entity_ids be unique across all Home Assistant instances.

<img src="meta/MQTT-Diagram.png" width="600">

Although these components primarily support ISY994 switch, light, fan components they will work with many other components like sensor, binary_sensor. Give them a try.

### Configuration
For the mqtt_sharehost you must specify the MQTT ```base_topic```. The rest of the configuration is to specify the entities to share on the MQTT server. Look at the Include/exclude section of the [MQTT Statestream](https://www.home-assistant.io/components/mqtt_statestream/) component for details on how to configure this part of the configuration.

```yaml
mqtt_sharehost:
  base_topic: hass_share
  include:
    entities:
      - switch.studio_state
      - switch.studio_christmas_lights
```

For the mqtt_shareclient all you need to do is specify MQTT ```base_topic``` and it will automatically pick all shared entities.
```yaml
mqtt_shareclient:
  base_topic: hass_share
```
