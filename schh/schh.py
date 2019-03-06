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
        self.activity_id = -1
        self.activity_name = "Power Off"
        self.command_map = {}
        if self._connect():
            self.harmony.disconnect()

    def _reset_state_info(self):
        """Resets state-related members to their defaults"""
        self.config = None
        self.activity_id = -1
        self.activity_name = "Power Off"
        self.command_map = {}

    def _close(self):
        """Closes the connectoion to the Harmony Hub"""
        self.harmony.disconnect()
        self._reset_state_info()

    def _connect(self):
        """Connects to the Harmony Hub"""
        try:
            self.harmony = harmony_client.create_and_connect_client(self.remote_address, 5222)
            if not self.harmony:
                self.harmony = None
                print("Failed to connect to Harmony Hub!")
                return False
            self.config = self.harmony.get_config()
            self.activity_id = self.harmony.get_current_activity()
            activity = [x for x in self.config["activity"] if int(x["id"]) == self.activity_id][0]
            if type(activity) is dict:
                self.activity_name = activity["label"]
            return True
        except Error as e:
            print("Caught exception while connecting!")
            print(e)
        return False

    def _get_channel_separator(self):
        return "."

    def _get_commands_payload(self, commands):
        return ["addFromVanilla", {"harmony_hub_command": commands}]

    def _get_activities_payload(self, activities):
        return ["addFromVanilla", {"harmony_hub_activities_name": activities}]

    def _get_update_payload(self):
        operations = []
        activities = []
        commands = []
        self.command_map = {}
        for activity in self.config["activity"]:
            activities.append(activity["label"])
            for cgroups in activity["controlGroup"]:
                for fncn in cgroups["function"]:
                    (label_key, voice_command) = self._label_to_key_and_voice_command(fncn["label"], activity["id"])
                    commands.append(voice_command)
                    self.command_map[label_key] = {}
                    self.command_map[label_key]["command"] = fncn["name"]
                    ridx = fncn["action"].rfind("\"")
                    idx = fncn["action"].find("deviceId")
                    if idx == -1:
                        idx = ridx - 8
                    else:
                        idx += 11
                    self.command_map[label_key]["device"] = fncn["action"][idx:ridx]

        operations.append(self._get_activities_payload(activities))
        operations.append(self._get_commands_payload(list(set(commands))))
        payload = {"operations": operations}
        return json.dumps(payload)

    def _label_to_key_and_voice_command(self, label, activity):
        if label == "0":
            label = "zero"
        elif label == "1":
            label = "one"
        elif label == "2":
            label = "two"
        elif label == "3":
            label = "three"
        elif label == "4":
            label = "four"
        elif label == "5":
            label = "five"
        elif label == "6":
            label = "six"
        elif label == "7":
            label = "seven"
        elif label == "8":
            label = "eight"
        elif label == "9":
            label = "nine"

        voice_command = label
        return (activity + "_" + label.lower().replace(" ", "_"), voice_command)

    def _map_command(self, command):
        """Maps from a command label to a command"""
        label_key = self._label_to_key_and_voice_command(command, str(self.activity_id))[0]
        if label_key in self.command_map.keys():
            return self.command_map[label_key]
        return None

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
            if len(channel_slot) > idx:
                sub_channel = int(channel_slot[idx])
                if len(channel_slot) > idx+1 and int(channel_slot[idx+1]) >= 5:
                    sub_channel += 1
                which_channel += str(sub_channel)

        if not self._connect():
            return False
        self.harmony.change_channel(which_channel)
        self._close()
        return True

    def send_command(self, command, repeat):
        """Sends command to the Harmony Hub repeat times"""
        if not self._connect():
            return 0
        mapped_command = self._map_command(command)
        if mapped_command is None:
            return -1
        for _ in range(repeat):
            self.harmony.send_command(mapped_command["device"], mapped_command["command"], 0.1)
        self._close()
        return 1

    def current_activity(self):
        """Returns the ID and name of the current activity"""
        if not self._connect():
            return False
        return_values = (self.activity_id, self.activity_name)
        self._close()
        return return_values

    def start_activity(self, activity_name):
        """Starts an activity on the Harmony Hub"""
        if not self._connect():
            return -1
        if activity_name == self.activity_name:
            print("current activity is the same as what was requested, doing nothing")
            return -2

        activities = [x for x in self.config["activity"] if x["label"] == activity_name]
        if activities is None:
            print("Cannot find the activity: {} ".format(activity_name))
            return -3
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
        if not self._connect():
            return False
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
        return True

__all__ = ["SmartCommandsHarmonyHub"]
