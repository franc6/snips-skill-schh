#!/usr/bin/env python3
"""Snips skill action for Harmony Hub"""
import gettext
import locale
from subprocess import Popen, PIPE, STDOUT

from snipskit.hermes.apps import HermesSnipsApp
from snipskit.config import AppConfig
from snipskit.hermes.decorators import intent

locale.setlocale(locale.LC_ALL, '')
gettext.bindtextdomain('messages', 'locales')
gettext = gettext.gettext

class SCHHActions(HermesSnipsApp):
    skill = False

    def _send_command(self, hermes, intent_message, which_command, repeat, delay=0.1):
        print("self._send_command: ", which_command, repeat, delay)
        ret = self.skill.send_command(which_command, repeat, delay)
        if ret == -1:
            hermes.publish_end_session(intent_message.session_id,
                gettext("FAILED_CONNECT"))
        elif ret == 0:
            hermes.publish_end_session(intent_message.session_id,
                gettext("COMMAND_NOT_FOUND"))

    @intent('franc:harmony_hub_change_channel')
    def change_channel(self, hermes, intent_message):
        """Handles intent for changing the channel"""
        print("change_channel intent called")
        channel_slot = None
        if intent_message.slots is not None:
            if intent_message.slots.channel_number:
                channel_slot = str(intent_message.slots.channel_number[0].slot_value.value.value)

        if channel_slot is None:
            hermes.publish_end_session(intent_message.session_id,
                gettext("NO_CHANNEL_GIVEN"))
            return

        ret = self.skill.change_channel(channel_slot)
        if ret == -1:
            hermes.publish_end_session(intent_message.session_id,
                gettext("FAILED_CONNECT"))
        elif ret == 0:
            hermes.publish_end_session(intent_message.session_id,
                gettext("FAILED_CHANGE_CHANNEL"))

    @intent('franc:harmony_hub_volume')
    def change_volume(self, hermes, intent_message):
        """Handles intent for changing the volume"""
        print("change_volume intent called")
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

        self._send_command(hermes, intent_message, which_command, repeat)

    @intent('franc:harmony_hub_channel_surf')
    def channel_surf(self, hermes, intent_message):
        self._send_command(hermes, intent_message, "ChannelUp", 40, 8)

    @intent('franc:harmony_hub_send_command')
    def send_command(self, hermes, intent_message):
        """Handles intent for sending a command"""
        print("send_command intent called")
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

        self._send_command(hermes, intent_message, which_command, repeat)

    @intent('franc:harmony_hub_power_on')
    def power_on(self, hermes, intent_message):
        """Handles intent for power on (starting an activity)"""
        print("power_on intent called")
        activity = None
        if intent_message.slots is not None:
            if intent_message.slots.activity:
                activity = intent_message.slots.activity[0].slot_value.value.value

        if activity is None:
            hermes.publish_end_session(intent_message.session_id,
                gettext("NO_ACTIVITY_GIVEN"))
            return

        ret = self.skill.start_activity(activity)
        if ret == 1:
            sentence = gettext("STARTED_ACTIVITY").format(activity=activity)
        elif ret == -1:
            sentence = gettext("FAILED_CONNECT")
        elif ret == -2:
            sentence = gettext("ACTIVITY_ALREADY_STARTED").format(activity=activity)
        elif ret == -3:
            sentence = gettext("ACTIVITY_UNKNOWN").format(activity=activity)
        else:
            sentence = gettext("FAILED_START_ACTIVITY").format(activity=activity)
        hermes.publish_end_session(intent_message.session_id, sentence)

    @intent('franc:harmony_hub_list_activities')
    def list_activities(self, hermes, intent_message):
        """Handles intent for listing activities"""
        print("list_activities intent called")

        activities = self.skill.list_activities()
        if isinstance(activities, int) and activities == -1:
            sentence = gettext("FAILED_CONNECT")
        elif len(activities) == 0:
            sentence = gettext("NO_ACTIVITIES_ON_HUB")
        else:
            act_sentence = ''
            for activity in activities:
                act_sentence += ',,.. ' + activity
            sentence = gettext("ACTIVITIES_LIST").format(activities=act_sentence)

        print(sentence)
        hermes.publish_end_session(intent_message.session_id, sentence)

    @intent('franc:harmony_hub_which_activity')
    def which_activity(self, hermes, intent_message):
        """Handles intent for listing which activity is current"""
        print("which_activities intent called")

        ret_value = self.skill.current_activity()
        if isinstance(ret_value, int) and ret_value == -1:
            sentence = gettext("FAILED_CONNECT")
        else:
            (activity_id, activity_name) = ret_value
            sentence = gettext("CURRENT_ACTIVITY").format(activity=activity_name)
        hermes.publish_end_session(intent_message.session_id, sentence)

    def inject_activities(self):
        payload = self.skill.get_injection_payload()
        self.hermes.request_injection(payload)

    def initialize(self):
        if self.config["secret"]["control"] == "XMPP":
            from schh.schh import SmartCommandsHarmonyHub
        else:
            from schh.schhaio import SmartCommandsHarmonyHub
        self.skill = SmartCommandsHarmonyHub(self.config["secret"]["remotename"])
        if isinstance(self.skill, bool):
            print("Could not create SmartCommandsHarmonyHub!")

        self.inject_activities()

        if isinstance(self.skill, bool):
            print("self.skill is now a bool?!")


if __name__ == "__main__":
    SCHHActions(config=AppConfig())
