"""
Hosts a set of configured entities on MQTT. Publishes state changes and
isy994_control events. Listens to call_service events.

Primarily intended to share entities between multiple Home Assistant instances.

For more details about this component, please refer to the documentation at
https://github.com/mikelawrence/homeassistant-custom-components
"""
import asyncio
import logging
import json
import voluptuous as vol

from homeassistant.const import (CONF_DOMAINS, CONF_ENTITIES, CONF_EXCLUDE,
    CONF_INCLUDE, MATCH_ALL, ATTR_ENTITY_ID, ATTR_DOMAIN, ATTR_SERVICE,
    ATTR_SERVICE_DATA, EVENT_CALL_SERVICE)
from homeassistant.core import (callback, EventOrigin)
from homeassistant.components.mqtt import (valid_publish_topic)
from homeassistant.helpers.entityfilter import generate_filter
from homeassistant.helpers.event import async_track_state_change
from homeassistant.helpers.json import JSONEncoder
import homeassistant.helpers.config_validation as cv


CONF_BASE_TOPIC = 'base_topic'

DEPENDENCIES = ['mqtt']

DOMAIN = 'mqtt_sharehost'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(CONF_EXCLUDE, default={}): vol.Schema({
            vol.Optional(CONF_ENTITIES, default=[]): cv.entity_ids,
            vol.Optional(CONF_DOMAINS, default=[]):
                vol.All(cv.ensure_list, [cv.string])
        }),
        vol.Optional(CONF_INCLUDE, default={}): vol.Schema({
            vol.Optional(CONF_ENTITIES, default=[]): cv.entity_ids,
            vol.Optional(CONF_DOMAINS, default=[]):
                vol.All(cv.ensure_list, [cv.string])
        }),
        vol.Required(CONF_BASE_TOPIC): valid_publish_topic
    })
}, extra=vol.ALLOW_EXTRA)

_LOGGER = logging.getLogger(__name__)

@asyncio.coroutine
def async_setup(hass, config):
    """Set up the MQTT state feed."""
    mqtt = hass.components.mqtt
    conf = config.get(DOMAIN, {})
    base_topic = conf.get(CONF_BASE_TOPIC)
    if not base_topic.endswith('/'):
        base_topic = base_topic + '/'
    event_topic = base_topic + 'event'
    control_topic = base_topic + 'control'
    pub_include = conf.get(CONF_INCLUDE, {})
    pub_exclude = conf.get(CONF_EXCLUDE, {})
    publish_filter = generate_filter(pub_include.get(CONF_DOMAINS, []),
                                     pub_include.get(CONF_ENTITIES, []),
                                     pub_exclude.get(CONF_DOMAINS, []),
                                     pub_exclude.get(CONF_ENTITIES, []))

    @callback
    def _control_listener(msg):
        """Receive remote control events from mqtt_shareclient."""
        # split = msg.topic.split('/')
        # domain = split[1]
        # object_id = split[2]
        # entity_id = domain + '.' + object_id
        # must be an entity we are configured to listen for commands
        # if not publish_filter(entity_id):
        #     return
        # process payload as JSON
        event = json.loads(msg.payload)
        # # must be a call_service event_type
        # #  not really necessary because only call_service events are published
        # if event.get('event_type') != EVENT_CALL_SERVICE:
        #     return
        event_data = event.get('event_data')
        domain = event_data.get(ATTR_DOMAIN)
        service = event_data.get(ATTR_SERVICE)
        data = event_data.get(ATTR_SERVICE_DATA)
        hass.async_add_job(hass.services.async_call(domain, service, data))
        # event_type = event.get('event_type')
        # _LOGGER.warning("Received remote {} event, data={}".format(
        #                 event_type, event_data))

    # subscribe to all control topics
    yield from mqtt.async_subscribe(control_topic, _control_listener)

    @callback
    def _state_publisher(entity_id, old_state, new_state):
        """Publish local states to mqtt_shareclient."""
        if new_state is None:
            return
        # do not publish entities not configured
        if not publish_filter(entity_id):
            return
        # start the current state dictionary
        state = { "state": new_state.state }
        state.update(dict(new_state.attributes))
        # convert state dictionary into JSON
        payload = json.dumps(state, cls=JSONEncoder)
        # create topic from entity_id
        topic = base_topic + entity_id.replace('.', '/') + '/state'
        # publish the topic, retain should be on for state topics
        hass.components.mqtt.async_publish(topic, payload, 0, True)
        # _LOGGER.warning("Published state for '{}', state={}".format(
        #   entity_id, payload))

    # asynchronous receive state changes
    async_track_state_change(hass, MATCH_ALL, _state_publisher)

    @callback
    def _event_publisher(event):
        """Publish local isy994_control events to mqtt_shareclient."""
        # we only publish local events
        if event.origin != EventOrigin.local:
            return
        # must be isy994_control event
        if event.event_type != 'isy994_control':
            return
        entity_id = event.data.get(ATTR_ENTITY_ID)
        # must be one of our entities
        if not publish_filter(entity_id):
            return
        event_info = {'event_type': event.event_type,
                      'event_data': event.data}
        payload = json.dumps(event_info, cls=JSONEncoder)
        # publish the topic, retain should be off for events
        hass.components.mqtt.async_publish(event_topic, payload, 0, False)
        # _LOGGER.warning("Publish local event '{}' data={}".format(
        #     event.event_type, event.data))

    # listen for local events if you are going to publish them.
    hass.bus.async_listen(MATCH_ALL, _event_publisher)

    return True
