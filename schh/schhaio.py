"""Provides SmartCommandsHarmonyHub for smarter interaction with a HarmonyHub"""
import asyncio
from functools import partial
import json
from subprocess import Popen, PIPE, STDOUT
from threading import Thread

from aioharmony.harmonyapi import HarmonyAPI
from aioharmony.const import SendCommandDevice

class SmartCommandsHarmonyHub:
    """Class for interacting with a Harmony Hub in a smarter way"""
    def __init__(self, remote_address):
        """Initialize members

        remote_address: The host name or IP address of the Harmony Hub
        """
        self.loop = asyncio.new_event_loop()
        self.thread = Thread(target=self._asyncio_thread_loop)
        self.thread.start()
        self.remote_address = remote_address
        self.config = None
        self.activity_id = -1
        self.activity_name = "Power Off"
        self.command_map = {}

    def _asyncio_thread_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def _stop_event_loop(self):
        self.loop.stop()
        return self.loop.is_running()

    def _reset_state_info(self):
        """Resets state-related members to their defaults"""
        self.config = None
        self.activity_id = -1
        self.activity_name = "Power Off"

    async def _run_in_loop2(self, co_routine):
        # Call _connect, if it returns -1, return -1 from here,
        api = await self._connect()
        if api == -1:
            return -1

        # Otherwise, carry on
        return_value = await co_routine(api)
        await self._close(api)
        return return_value

    def _run_in_loop(self, co_routine):
        future = asyncio.run_coroutine_threadsafe(
                self._run_in_loop2(co_routine),
                self.loop)
        return future.result()

    async def _close(self, api):
        """Closes the connectoion to the Harmony Hub"""
        await api.close()
        self._reset_state_info()

    async def _connect(self):
        """Connects to the Harmony Hub"""
        api = HarmonyAPI(ip_address=self.remote_address, loop=self.loop)
        if await api.connect():
            self.config = api.hub_config[0]
            (self.activity_id, self.activity_name) = api.current_activity
            return api
        return False

    def _get_channel_separator(self):
        return "."

    def _get_commands_payload(self, commands):
        return ["addFromVanilla", {"harmony_hub_command": commands}]

    def _get_activities_payload(self, activities):
        return ["addFromVanilla", {"harmony_hub_activities_name": activities}]

    async def _get_update_payload(self, _):
        """ Finds all the commands and returns a payload for injecting
        commands """
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
                    # Initialize command to fncn["name"], in case we
                    # can't find better
                    self.command_map[label_key]["command"] = fncn["name"]
                    # Find better...
                    idx = fncn["action"].find("command")
                    if idx != -1:
                        idx += 10
                        ridx = fncn["action"].find("\"", idx)
                        if ridx != -1:
                            self.command_map[label_key]["command"] = fncn["action"][idx:ridx]
                    # Next, find the device to use
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
        """ Return the key for command_map for the given label and activity"""
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

    async def _change_channel(self, which_channel, api):
        # Note that we have to call send_to_hub directly, because the
        # HarmonyAPI assumes channel must be an int, which doesn't work
        # with digital channels
        params = {
            'timestamp': 0,
            'channel': which_channel
        }
        response = await api._harmony_client.send_to_hub(
                command='change_channel',
                params=params)
        if not response:
            return 0
        return 1 if response.get('code') == 200 else 0

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

        return self._run_in_loop(partial(self._change_channel, which_channel))

    async def _send_command(self, command, repeat, api):
        mapped_command = self._map_command(command)
        if mapped_command is None:
            return 0
        send_commands = []
        for _ in range(repeat):
            send_commands.append(SendCommandDevice(device=mapped_command["device"], command=mapped_command["command"], delay=0.1))
        if len(send_commands) == 0:
            return 0
        await api.send_commands(send_commands)
        return 1

    def send_command(self, command, repeat):
        """Sends command to the Harmony Hub repeat times"""
        return self._run_in_loop(partial(self._send_command, command, repeat))

    async def _list_activities(self, _):
        activities = []
        for x in self.config["activity"]:
            activities.append(x["label"])
        return activities

    def list_activities(self):
        """Returns a list of activities"""
        return self._run_in_loop(partial(self._list_activities))

    async def _current_activity(self, _):
        return (self.activity_id, self.activity_name)

    def current_activity(self):
        """Returns the ID and name of the current activity"""
        return self._run_in_loop(partial(self._current_activity))

    async def _start_activity(self, activity_name, api):
        if activity_name == self.activity_name:
            return -2

        activity_id = api.get_activity_id(activity_name)

        if activity_id is None:
            return -3

        ret_value = await api.start_activity(activity_id)
        if ret_value:
            return 1

        return 0

    def start_activity(self, activity_name):
        """Starts an activity on the Harmony Hub"""
        return self._run_in_loop(partial(self._start_activity, activity_name))

    def power_off(self):
        """Sets the current activity of the Harmony Hub to -1, AKA "PowerOff"."""
        return self.start_activity("PowerOff")

    def inject_activities(self):
        """Injects the list of activities known to the Harmony Hub"""
        payload = self._run_in_loop(partial(self._get_update_payload))
        if payload == -1:
            return -1
        payload = payload + "\n"
        pipe = Popen(["/usr/bin/mosquitto_pub",
                      "-t",
                      "hermes/injection/perform",
                      "-l"
                     ],
                     stdin=PIPE,
                     stdout=PIPE,
                     stderr=STDOUT)
        pipe.communicate(input=payload.encode("utf-8"))
        return 1

    def close(self):
        future = asyncio.run_coroutine_threadsafe(
                self._stop_event_loop(),
                self.loop)
        self.thread.join()
        return

__all__ = ["SmartCommandsHarmonyHub"]
