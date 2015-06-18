# Raspberry Pi CNC
Web interface for controlling GRBL via a Raspberry Pi

![Raspberry Pi CNC Web interface](/static/img/Raspberry-Pi-CNC-User-Interface.png?raw=true )

Features:
- Single Command Mode: In this mode only one command is sent to GRBL(G-Code Enterpeter) at a time. It will wait for the machine to go into idle mode before the next g-code command is sent. 
- Command routing. Create custom commands, example: Run a Python script to send notifications or shut down the system once the job has finished. Example command "RUNPYTHON" - This will ping the local host.


# Disclaimer
  The software is made available "AS IS". It is in an early stage of development.  Hence there should be plenty of bugs not yet spotted. Please use/try it with care, I don't want to be liable if it causes
  any damage :)
