"""Provides SmartCommandsHarmonyHub for smarter interaction with a HarmonyHub"""
import json
from subprocess import Popen, PIPE, STDOUT
from pyharmony import client as harmony_client

class SmartCommandsHarmonyHub:
    """Class for interacting with a Harmony Hub in a smarter way"""
    def __init__(self, remote_address):
        """Initialize members

        remote_address: The host name or IP address of the Harmony Hub
        """
        self.remote_address = remote_address
        self.config = None
        self.main_device = -1
        self.volume_device = -1
        self.activity_id = -1
        self.activity_name = "Power Off"
        self._connect()

    def _reset_state_info(self):
        """Resets state-related members to their defaults"""
        self.config = None
        self.main_device = -1
        self.volume_device = -1
        self.activity_id = -1
        self.activity_name = "Power Off"

    def _close(self):
        """Closes the connectoion to the Harmony Hub"""
        self.harmony.disconnect()
        self._reset_state_info()

    def _connect(self):
        """Connects to the Harmony Hub"""
        self.harmony = harmony_client.create_and_connect_client(self.remote_address, 5222)
        self.config = self.harmony.get_config()
        self.activity_id = self.harmony.get_current_activity()
        activity = [x for x in self.config["activity"] if int(x["id"]) == self.activity_id][0]
        if type(activity) is dict:
            self.activity_name = activity["label"]

    def _get_devices_for_activity(self):
        """Gets the main and volume devices for the current activity"""
        self.main_device = -1
        self.volume_device = -1
        if self.activity_id == -1:
            return

        act = next((x for x in self.config["activity"]
                    if x["label"] == self.activity_name), None)
        if act is not None:
            #print(json.dumps(act, indent=4, separators=(",", ": ")))
            if "ChannelChangingActivityRole" in act.keys():
                self.main_device = act["ChannelChangingActivityRole"]
            elif "roles" in act.keys() and "ChannelChangingActivityRole" in act["roles"].keys():
                self.main_device = act["roles"]["ChannelChangingActivityRole"]
            elif "roles" in act.keys() and "PlayMediaActivityRole" in act["roles"].keys():
                self.main_device = act["roles"]["PlayMediaActivityRole"]
            elif "roles" in act.keys() and "PlayMovieActivityRole" in act["roles"].keys():
                self.main_device = act["roles"]["PlayMovieActivityRole"]

            if "VolumeActivityRole" in act.keys():
                self.volume_device = act["VolumeActivityRole"]
            elif "roles" in act.keys() and "VolumeActivityRole" in act["roles"].keys():
                self.volume_device = act["roles"]["VolumeActivityRole"]

    def _get_channel_separator(self):
        return "."

    def _get_device_for_command(self, command):
        self._get_devices_for_activity()
        if (command == "VolumeUp") or (command == "VolumeDown") or (command == "Mute"):
            return self.volume_device
        return self.main_device

    def _get_activities_payload(self, activities):
        return ["addFromVanilla", {"harmony_hub_activities_name": activities}]

    def _get_update_payload(self):
        operations = []
        activities = []
        for activity in self.config["activity"]:
            activities.append(activity["label"])

        operations.append(self._get_activities_payload(activities))
        payload = {"operations": operations}
        return json.dumps(payload)

    def change_channel(self, channel_slot):
        """Changes to the specified channel, being sure that if digital
        channels are used, that it uses the correct separator style.
        """
        which_channel = ""
        dot_reached = False
        sub_channel = 0
        for idx in range(len(channel_slot)):
            if channel_slot[idx].isdigit() and not dot_reached:
                which_channel += channel_slot[idx]
            elif channel_slot[idx] == "." or channel_slot[idx] == ",":
                which_channel += self._get_channel_separator()
                dot_reached = True
                idx += 1
                break

        if dot_reached:
            sub_channel = int(channel_slot[idx])
            if int(channel_slot[idx+1]) >= 5:
                sub_channel += 1
            which_channel += str(sub_channel)
        self._connect()
        self.harmony.change_channel(which_channel)
        self._close()
        return

    def send_command(self, command, repeat):
        """Sends command to the Harmony Hub repeat times"""
        self._connect()
        device = self._get_device_for_command(command)
        for _ in range(repeat):
            self.harmony.send_command(device, command, 0.1)
        self._close()
        return

    def current_activity(self):
        """Returns the ID and name of the current activity"""
        self._connect()
        return_values = (self.activity_id, self.activity_name)
        self._close()
        return return_values

    def start_activity(self, activity_name):
        """Starts an activity on the Harmony Hub"""
        self._connect()
        if activity_name == self.activity_name:
            print("current activity is the same as what was requested, doing nothing")
            return -1

        activities = [x for x in self.config["activity"] if x["label"] == activity_name]
        if activities is None:
            print("Cannot find the activity: {} ".format(activity_name))
            return -1
        activity = activities[0]

        if type(activity) is dict:
            activity_id = activity["id"]
        return_value = self.harmony.start_activity(activity_id)
        self._close()
        return 1 if return_value else 0

    def power_off(self):
        """Sets the current activity of the Harmony Hub to -1, AKA "PowerOff"."""
        return self.start_activity("PowerOff")

    def inject_activities(self):
        """Injects the list of activities known to the Harmony Hub"""
        self._connect()
        payload = self._get_update_payload() + "\n"
        pipe = Popen(["/usr/bin/mosquitto_pub",
                      "-t",
                      "hermes/injection/perform",
                      "-l"
                     ],
                     stdin=PIPE,
                     stdout=PIPE,
                     stderr=STDOUT)
        pipe.communicate(input=payload.encode("utf-8"))
        self._close()

__all__ = ["SmartCommandsHarmonyHub"]
