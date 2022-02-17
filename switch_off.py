import time
from orvibo.s20 import S20, discover

hosts = discover() # Discover devices on your local network.
host = next(iter(hosts))
s20 = S20(host) # Use a discovered host, or supply a known host.
s20.on = False # Turn it off.

