# snips-skill-schh
Snips skill for interacting with a Harmony Hub as a remote control for an
entertainment system.

This project provides a skill which handles the Harmony Hub in a context-aware
manner.  You do not need to specify to which device a command should be sent,
as that will be determined based on your Harmony Hub configuration.  Note this
isn't complete yet, as it really only detects a "main" device and a "volume"
device.

As you encounter situations where this isn't good enough, create an issue and
note the following:

1. The actual command you tried to send
2. The device it should have been sent to
3. The device it did send the command to
4. The ID of the activity that was active
5. A dump of the activities and devices configuration (python3 -m pyharmony --harmony_ip &lt;remotename&gt; show_config)


