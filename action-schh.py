#!/usr/bin/env python3
"""Snips skill action for Harmony Hub"""
import configparser
import gettext
import locale
from hermes_python.hermes import Hermes
from hermes_python.ontology import *

locale.setlocale(locale.LC_ALL, '')
gettext.bindtextdomain('messages', 'locales')
gettext = gettext.gettext

CONFIG_INI = "config.ini"
CONFIG_ENCODING = "utf-8"

class  SnipsConfigParser(configparser.ConfigParser):
    """Subclass ConfigParser.SafeConfigParser to add to_dict method."""
    def to_dict(self):
        """Returns a dictionary of sections and options from the config file"""
        return {section: {option_name : option for option_name,
                          option in self.items(section)} for section in self.sections()}

def read_configuration_file(file_name):
    """Reads and parses file_name.  Returns a dictionary based on its contents"""
    try:
        config_parser = SnipsConfigParser()
        config_parser.read(file_name)
        return config_parser.to_dict()
    except (IOError, configparser.Error):
        return dict()

def _send_command(hermes, intent_message, which_command, repeat):
    print("_send_command: ", which_command, repeat)
    ret = hermes.skill.send_command(which_command, repeat)
    if ret == -1:
        hermes.publish_end_session(intent_message.session_id,
            gettext("FAILED_CONNECT"))
    elif ret == 0:
        hermes.publish_end_session(intent_message.session_id,
            gettext("COMMAND_NOT_FOUND"))

def change_channel(hermes, intent_message):
    """Handles intent for changing the channel"""
    channel_slot = None
    repeat = 1
    if intent_message.slots is not None:
        if intent_message.slots.channel_number:
            channel_slot = str(intent_message.slots.channel_number[0].slot_value.value.value)

    if channel_slot is None:
        hermes.publish_end_session(intent_message.session_id,
            gettext("NO_CHANNEL_GIVEN"))
        return

    ret = hermes.skill.change_channel(channel_slot)
    if ret == -1:
        hermes.publish_end_session(intent_message.session_id,
            gettext("FAILED_CONNECT"))
    elif ret == 0:
        hermes.publish_end_session(intent_message.session_id,
            gettext("FAILED_CHANGE_CHANNEL"))

def change_volume(hermes, intent_message):
    """Handles intent for changing the volume"""
    which_command = None
    repeat = 1
    if intent_message.slots is not None:
        if intent_message.slots.updownmute:
            which_command = intent_message.slots.updownmute[0].slot_value.value.value
        if intent_message.slots.repeat:
            repeat = int(float(intent_message.slots.repeat[0].slot_value.value.value))

    if which_command is None:
        hermes.publish_end_session(intent_message.session_id,
            gettext("NO_VOLUME_GIVEN"))
        return

    _send_command(hermes, intent_message, which_command, repeat)

def send_command(hermes, intent_message):
    """Handles intent for sending a command"""
    which_command = None
    repeat = 1
    if intent_message.slots is not None:
        if intent_message.slots.command:
            which_command = intent_message.slots.command[0].slot_value.value.value
        if intent_message.slots.repeat:
            repeat = int(float(intent_message.slots.repeat[0].slot_value.value.value))

    if which_command is None:
        hermes.publish_end_session(intent_message.session_id,
            gettext("NO_COMMAND_GIVEN"))
        return

    _send_command(hermes, intent_message, which_command, repeat)

def power_on(hermes, intent_message):
    """Handles intent for power on (starting an activity)"""
    activity = None
    if intent_message.slots is not None:
        if intent_message.slots.activity:
            activity = intent_message.slots.activity[0].slot_value.value.value

    if activity is None:
        hermes.publish_end_session(intent_message.session_id,
            gettext("NO_ACTIVITY_GIVEN"))
        return

    ret = hermes.skill.start_activity(activity)
    if ret == 1:
        sentence = gettext("STARTED_ACTIVITY").format(activity=activity)
    elif ret == -1:
        sentence = gettext("FAILED_CONNECT"))
    elif ret == -2:
        sentence = gettext("ACTIVITY_ALREADY_STARTED").format(activity=activity)
    elif ret == -3:
        sentence = gettext("ACTIVITY_UNKNOWN").format(activity=activity)
    else:
        sentence = gettext("FAILED_START_ACTIVITY").format(activity=activity)
    hermes.publish_end_session(intent_message.session_id, sentence)

def list_activities(hermes, intent_message):
    """Handles intent for listing activities"""

    activities = hermes.skill.list_activities()
    if isinstance(activities, int) and activities == -1:
        sentence = gettext("FAILED_CONNECT"))
    elif len(activities) == 0:
        sentence = gettext("NO_ACTIVITIES_ON_HUB")
    else:
        act_sentence = ''
        for activity in activities:
            act_sentence += ',,.. ' + activity
        sentence = gettext("ACTIVITIES_LIST").format(activities=act_sentence)

    hermes.publish_end_session(intent_message.session_id, sentence)

def which_activity(hermes, intent_message):
    """Handles intent for listing which activity is current"""

    ret_value = hermes.skill.current_activity()
    if isinstance(ret_value, int) and ret_value == -1:
        sentence = gettext("FAILED_CONNECT")
    else:
        (activity_id, activity_name) = ret_value
        sentence = gettext("CURRENT_ACTIVITY").format(activity=activity_name)
    hermes.publish_end_session(intent_message.session_id, sentence)

def main(hermes):
    """main function"""
    config = read_configuration_file(CONFIG_INI)
    if config["secret"]["control"] == "XMPP":
        from schh.schh import SmartCommandsHarmonyHub
    else:
        from schh.schhaio import SmartCommandsHarmonyHub
    hermes.skill = SmartCommandsHarmonyHub(config["secret"]["remotename"])

    hermes.skill.inject_activities()

    hermes.subscribe_intent("franc:harmony_hub_volume", change_volume) \
          .subscribe_intent("franc:harmony_hub_send_command", send_command) \
          .subscribe_intent("franc:harmony_hub_power_on", power_on) \
          .subscribe_intent("franc:harmony_hub_change_channel", change_channel) \
          .subscribe_intent("franc:harmony_hub_list_activities", list_activities) \
          .subscribe_intent("franc:harmony_hub_which_activity", which_activity) \
          .loop_forever()

    print("loop_forever returned!")
    hermes.skill.close()

if __name__ == "__main__":
    with Hermes("localhost:1883") as h:
        main(h)
