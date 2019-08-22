# snips-skill-schh
[![License](https://img.shields.io/github/license/franc6/snips-skill-schh.svg)](https://github.com/franc6/snips-skill-schh/blob/master/LICENSE)

Snips skill for interacting with a Harmony Hub as a remote control for
an entertainment system.

This project provides a skill which handles the Harmony Hub in a
context-aware manner.  You do not need to specify to which device a
command should be sent, as that will be determined based on your Harmony
Hub configuration.


## What can I do with it?
* Start an activity on the Harmony Hub
* Change the channel directly, including to digital TV channels
* Send commands to the appropriate device via the Harmony Hub
* List all of the activities on the Harmony Hub
* List the current activity of the Harmony Hub
* Power off your devices (start the "Power Off" activity)

See examples in my Harmony Hub app for snips.


## Configuration Notes
All configuration is done in config.ini, in the "secret" section.

Name | Value
---- | -----
remotename | The name or IP address of your Harmony Hub
control    | "XMPP" or "AIO", indicates which control style to use


## Technical Notes
For now, use of XMPP is more reliable than AIO.  There are some bad
interactions between hermes-python and asyncio.  I'm still trying to
correct it without making it too slow to be useful

[![Buy me some pizza](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/qpunYPZx5)
