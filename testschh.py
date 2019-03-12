#!/usr/bin/env python3

import datetime
import sys
from threading import Thread
from time import sleep

# You must pick one of the two lines, not both!
from schh.schhaio import SmartCommandsHarmonyHub
from schh.schh import SmartCommandsHarmonyHub

# Enter the name or IP Address of your Harmony Hub
MY_HUB="harmony_hub"
# Enter the name of an activity other than "PowerOff" or "Watch TV"
test_activity = "Listen to Music"

def list_activities(skill):
    activities = skill.list_activities()

    print("all activities: ", activities)
    return

def current_activity(skill):
    print("current activity: ", skill.current_activity())
    return

def start_activity(skill, activity):
    print("start_activity: ", activity, skill.start_activity(activity))
    return

def change_channel(skill, channel):
    print("change_channel: ", channel, skill.change_channel(channel))
    return

def send_command(skill, command, repeat):
    print("send_command: ", command, repeat,
            skill.send_command(command, repeat))
    return

def power_off(skill):
    print("power_off: ", skill.power_off())
    return


if __name__ == '__main__':
    start_time = datetime.datetime.now()
    skill = SmartCommandsHarmonyHub(MY_HUB)
    # Note that inject_activities must be called.  If it causes problems,
    # just disable the code in it that invokes mosquitto_pub
    skill.inject_activities()

    t1 = Thread(target=list_activities, args=(skill,))
    t1.start()
    t1.join()

    t2 = Thread(target=current_activity, args=(skill,))
    t2.start()
    t2.join()


    t2 = Thread(target=start_activity, args=(skill,test_activity))
    t2.start()
    t2.join()

    sleep(20)

    t2 = Thread(target=current_activity, args=(skill,))
    t2.start()
    t2.join()

    t2 = Thread(target=start_activity, args=(skill,"Watch TV"))
    t2.start()
    t2.join()

    t2 = Thread(target=current_activity, args=(skill,))
    t2.start()
    t2.join()

    t2 = Thread(target=change_channel, args=(skill,"0"))
    t2.start()
    t2.join()

    t2 = Thread(target=change_channel, args=(skill,"2.2"))
    t2.start()
    t2.join()

    t2 = Thread(target=send_command, args=(skill,"Channel Up", 2))
    t2.start()
    t2.join()

    t2 = Thread(target=send_command, args=(skill,"Mute", 1))
    t2.start()
    t2.join()

    sleep(5)

    t2 = Thread(target=send_command, args=(skill,"Mute", 1))
    t2.start()
    t2.join()

    sleep(20)

    t2 = Thread(target=power_off, args=(skill,))
    t2.start()
    t2.join()

    skill.close()

    print("Began: ", start_time)
    print("Ended: ", datetime.datetime.now())
    sys.exit(0)
