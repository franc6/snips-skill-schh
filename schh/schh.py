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
        self.command_map = {}
        if self._connect():
            self.harmony.disconnect()

    def _reset_state_info(self):
        """Resets state-related members to their defaults"""
        self.config = None
        self.main_device = -1
        self.volume_device = -1
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
                    if fncn["label"] == "0":
                        commands.append("zero")
                        self.command_map["zero"] = fncn["name"]
                    elif fncn["label"] == "1":
                        commands.append("one")
                        self.command_map["one"] = fncn["name"]
                    elif fncn["label"] == "2":
                        commands.append("two")
                        self.command_map["two"] = fncn["name"]
                    elif fncn["label"] == "3":
                        commands.append("three")
                        self.command_map["three"] = fncn["name"]
                    elif fncn["label"] == "4":
                        commands.append("four")
                        self.command_map["four"] = fncn["name"]
                    elif fncn["label"] == "5":
                        commands.append("five")
                        self.command_map["five"] = fncn["name"]
                    elif fncn["label"] == "6":
                        commands.append("six")
                        self.command_map["six"] = fncn["name"]
                    elif fncn["label"] == "7":
                        commands.append("seven")
                        self.command_map["seven"] = fncn["name"]
                    elif fncn["label"] == "8":
                        commands.append("eight")
                        self.command_map["eight"] = fncn["name"]
                    elif fncn["label"] == "9":
                        commands.append("nine")
                        self.command_map["nine"] = fncn["name"]
                    else:
                        commands.append(fncn["label"])
                        self.command_map[fncn["label"]] = fncn["name"]

        operations.append(self._get_activities_payload(activities))
        operations.append(self._get_commands_payload(commands))
        payload = {"operations": operations}
        return json.dumps(payload)

    def _map_command(self, command):
        """Maps from a command label to a command"""
        if command in self.command_map.keys():
            return self.command_map[command]
        return command

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
            return False
        command = self._map_command(command)
        device = self._get_device_for_command(command)
        for _ in range(repeat):
            self.harmony.send_command(device, command, 0.1)
        self._close()
        return True

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
