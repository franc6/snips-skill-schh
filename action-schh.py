#!/usr/bin/env python3
"""Snips skill action for Harmony Hub"""
import configparser
from hermes_python.hermes import Hermes
from hermes_python.ontology import *
from schh.schh import SmartCommandsHarmonyHub

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
    ret = hermes.skill.send_command(which_command, repeat)
    if ret == 0:
        hermes.publish_end_session(intent_message.session_id,
            "I could not connect to the Harmony Hub.")
    elif ret == -1:
        hermes.publish_end_session(intent_message.session_id,
            "I could not determine what command to send to the Harmony Hub.")

def change_channel(hermes, intent_message):
    """Handles intent for changing the volume"""
    channel_slot = None
    repeat = 1
    if intent_message.slots is not None:
        if intent_message.slots.channel_number:
            channel_slot = str(intent_message.slots.channel_number[0].slot_value.value.value)

    if channel_slot is None:
        hermes.publish_end_session(intent_message.session_id,
            "I did not change the channel with the Harmony Hub.")
        return

    if not hermes.skill.change_channel(channel_slot):
        hermes.publish_end_session(intent_message.session_id,
            "I could not connect to the Harmony Hub.")

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
            "I did not change the volume with the Harmony Hub.")
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
            "I did not send a command to the Harmony Hub.")
        return

    _send_command(hermes, intent_message, which_command, repeat)

def power_on(hermes, intent_message):
    """Handles intent for power on (starting an activity)"""
    activity = None
    if intent_message.slots is not None:
        if intent_message.slots.activity:
            activity = intent_message.slots.activity[0].slot_value.value.value

    print("Received power_on intent")
    if activity is None:
        hermes.publish_end_session(intent_message.session_id,
            "I did not start an activity on the Harmony Hub.")
        return

    print("Starting activity: {}".format(activity))
    ret = hermes.skill.start_activity(activity)
    if ret == 1:
        sentence = "I started the {} activity on the Harmony Hub.".format(activity)
    elif ret == -1:
        sentence = "I could not connect to the Harmony Hub."
    elif ret == -2:
        sentence = "The {} activity is already started on the Harmony Hub.".format(activity)
    elif ret == -3:
        sentence = "I don't know how to start the {} activity.".format(activity)
    else:
        sentence = "I failed to started the {} activity on the Harmony Hub.".format(activity)
    hermes.publish_end_session(intent_message.session_id, sentence)

def main(hermes):
    """main function"""
    config = read_configuration_file(CONFIG_INI)
    hermes.skill = SmartCommandsHarmonyHub(config["secret"]["remotename"])

    hermes.skill.inject_activities()

    hermes.subscribe_intent("franc:harmony_hub_volume", change_volume) \
          .subscribe_intent("franc:harmony_hub_send_command", send_command) \
          .subscribe_intent("franc:harmony_hub_power_on", power_on) \
          .subscribe_intent("franc:harmony_hub_change_channel", change_channel) \
          .loop_forever()

    print("loop_forever returned!")

if __name__ == "__main__":
    with Hermes("localhost:1883") as h:
        main(h)
