import time
from orvibo.s20 import S20, discover

hosts = discover() # Discover devices on your local network.
host = next(iter(hosts))
print(host)
s20 = S20(host) # Use a discovered host, or supply a known host.
print(s20.on) # Current state (True = ON, False = OFF).
while True:
  s20.on = True # Turn it on.
  time.sleep(5)
  s20.on = False # Turn it off.
  time.sleep(5)

