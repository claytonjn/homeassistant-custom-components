"""The MQTT Shareclient component."""
import asyncio
import logging
import json
import voluptuous as vol

from homeassistant.const import (MATCH_ALL, ATTR_ENTITY_ID, ATTR_STATE,
    ATTR_SERVICE, ATTR_SERVICE_DATA, EVENT_CALL_SERVICE)
from homeassistant.core import (callback, EventOrigin)
from homeassistant.components.mqtt import (valid_publish_topic)
from homeassistant.helpers.json import JSONEncoder
import homeassistant.helpers.config_validation as cv

DOMAIN = 'mqtt_shareclient'

CONF_BASE_TOPIC = 'base_topic'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_BASE_TOPIC): valid_publish_topic
    })
}, extra=vol.ALLOW_EXTRA)

_LOGGER = logging.getLogger(__name__)
# all discovered entities
entities = {}
status_update = None

@asyncio.coroutine
def async_setup(hass, config):
    """Set up MQTT Share Client."""
    mqtt = hass.components.mqtt
    conf = config.get(DOMAIN, {})
    base_topic = conf.get(CONF_BASE_TOPIC)
    if not base_topic.endswith('/'):
        base_topic = base_topic + '/'
    event_topic = base_topic + 'event'
    control_topic = base_topic + 'control'
    state_topic = base_topic + "+/+/state"

    @callback
    def _state_listener(msg):
        """Receive remote states from mqtt_sharehost."""
        # get the entity_id from the topic
        split = msg.topic.split('/')
        domain = split[1]
        object_id = split[2]
        entity_id = domain + '.' + object_id
        # process payload as JSON
        values = json.loads(msg.payload)
        state = values.get(ATTR_STATE)
        values.pop(ATTR_STATE)          # state is not an attribute
        entities[entity_id] = True      # this was a remote status update
        hass.states.async_set(entity_id, state, values)
        # _LOGGER.debug("Received state for '%s', state=%s, attributes=%s",
        #     entity_id, state, values)

    # subscribe to all state topics
    yield from mqtt.async_subscribe(state_topic, _state_listener)

    @callback
    def _control_publisher(event):
        """Publish local call service events to mqtt_sharehost."""
        # must be a local event
        if event.origin != EventOrigin.local:
            return
        # must be a call_service event
        if event.event_type != EVENT_CALL_SERVICE:
            return
        service_data = event.data.get(ATTR_SERVICE_DATA)
        # entity_id in service_data can be a string or list of strings
        #   force it to always be a list
        if isinstance(service_data.get(ATTR_ENTITY_ID), list):
            entity_ids = service_data.get(ATTR_ENTITY_ID)
        else:
            entity_ids = [service_data.get(ATTR_ENTITY_ID)]
        # each entity_is published to its own topic
        for entity_id in entity_ids:
            # must be one of our entities
            if not entity_id in entities:
                break
            # update entity_id
            event.data[ATTR_SERVICE_DATA][ATTR_ENTITY_ID] = entity_id
            event_info = {'event_type': event.event_type,
                          'event_data': event.data}
            payload = json.dumps(event_info, cls=JSONEncoder)
            # publish the topic, retain should be off for events
            hass.components.mqtt.async_publish(control_topic, payload, 0, 
                False)
            # _LOGGER.debug("Publish local control event '%s' data=%s",
            #     event.event_type, event_info)

    # listen for local events.
    hass.bus.async_listen(MATCH_ALL, _control_publisher)

    @callback
    def _event_listener(msg):
        """Receive remote isy994_control events from mqtt_shareclient."""
        # process payload as JSON
        event = json.loads(msg.payload)
        event_type = event.get('event_type')
        event_data = event.get('event_data')
        # fire the event locally (origin is remote)
        hass.bus.async_fire(event_type, event_data=event_data,
                            origin=EventOrigin.remote)
        # _LOGGER.debug("Received remote event '%s', data=%s",
        #     event_type, event_data)

    # subscribe to all control topics
    yield from mqtt.async_subscribe(event_topic, _event_listener)
    return True
