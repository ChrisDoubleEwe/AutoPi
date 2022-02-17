import soco
import random
import time
import datetime
import pprint
from time import gmtime, strftime
import RPi.GPIO as GPIO

sensor = 4
GPIO.setmode(GPIO.BCM)
GPIO.setup(sensor, GPIO.IN, GPIO.PUD_DOWN)

previous_state = False
current_state = False
timer=0
sonos_playing = False

speakers = soco.discover()
kitchen_ip = ""
livingroom_ip = ""

# Get a list of speakers
for speaker in speakers:
  if speaker.player_name == "Kitchen":
    kitchen_ip = speaker.ip_address
    print("Kitchen IP = %s" % (kitchen_ip))
  if speaker.player_name == "Living Room":
    livingroom_ip = speaker.ip_address
    print("Living room IP = %s" % (livingroom_ip))


kitchen_sonos = soco.SoCo(kitchen_ip)
livingroom_sonos = soco.SoCo(livingroom_ip)
print("KTCHEN status: %s" % (kitchen_sonos.get_current_transport_info().get('current_transport_state')))
print("KTCHEN status: %s" % (kitchen_sonos.get_current_transport_info()))



def sonos_start():
  #playlists = kitchen_sonos.get_music_library_information("sonos_playlists")
  playlists = kitchen_sonos.get_sonos_playlists()
  print playlists 

  now = datetime.datetime.now()
  dayName = now.strftime("%A")
  dayMonth = now.strftime("%d%m")
  nowMonth = now.strftime("%m")
  nowDay = now.strftime("%d")
  nowHour = datetime.datetime.now().hour

  remember_playlist = playlists[0]

  #Default choice is Melanie's music...
  looking_for_playlist = "Melanie's Choice"
  maybe = random.randrange(0, 10)
  if maybe <= 4:
    looking_for_playlist = "Chris Choice";


  # Play Christmas songs as it gets progressively closer to Christmas
  if nowMonth == "12" and int(nowDay)<27 and int(nowDay)>10:
    maybe = random.randrange(0, 13)
    if (int(nowDay)-10 > maybe):
      looking_for_playlist = "Christmas"


 
  #  1 in 10 chance of playing a day-specific song
  maybe = random.randrange(0, 10)
  if maybe == 5:
    looking_for_playlist = dayName

  # If it's our birthday, play birthday songs
  if (dayMonth=="1409" or dayMonth=="1804"):
    if nowHour < 10:
      looking_for_playlist = "Birthday"
    else:
      maybe = random.randrange(0, 3)
      if maybe == 1:
        looking_for_playlist = "Birthday"

  for playlist in playlists:
    if playlist.title == looking_for_playlist:
      print playlist.title
      remember_playlist = playlist

  print("Queue length: %d" % (len(kitchen_sonos.get_queue())))

  if len(kitchen_sonos.get_queue()) == 0:
    print "Nothing in current queue. Adding a playlist"
    #kitchen_sonos.add_to_queue(kitchen_sonos.get_music_library_information("sonos_playlists")[1])
    kitchen_sonos.add_to_queue(remember_playlist)
    kitchen_sonos.play_mode = 'SHUFFLE'
  else:
    print "Queue already populated"

  # If KITCHEN and LIVINGROOM are both controller, that means the speakers are UNGROUPED
  if livingroom_sonos.is_coordinator and kitchen_sonos.is_coordinator:
    print "KITCHEN and LIVINGROOM are both controller, that means the speakers are UNGROUPED"
    #   If KITCHEN is playing, do nothing.
    if (kitchen_sonos.get_current_transport_info().get('current_transport_state') == "PLAYING"):
      # Do nothing. Kitchen sonos is already playing.
      print "Do nothing. Kitchen sonos is already playing."
    else: 
      #   If LIVINGROOM is playing, add KITCHEN to the group 
      if (livingroom_sonos.get_current_transport_info().get('current_transport_state') == "PLAYING"):
        print "LIVINGROOM is playing, add KITCHEN to the group"
        kitchen_sonos.join(livingroom_sonos)
      #   If LIVINGROOM is NOT playing, start KITCHEN
      else:
        track = random.randrange(0, (len(kitchen_sonos.get_queue()) -1))
        print("LIVINGROOM is NOT playing, start KITCHEN playing random track %d" % track)
        # For some reason, play() sometimes causes exceptions. play_from_queue seems to work at all times.
        #kitchen_sonos.play()
        kitchen_sonos.play_from_queue(track)
  # Otherwise, check the controller to see if music is currently playing:
  else:
    print "Speakers are GROUPED"
    #   If controller is playing, do nothing
    if (kitchen_sonos.group.coordinator.get_current_transport_info().get('current_transport_state') == "PLAYING"):
      # Do nothing. Kitchen sonos is already playing.
      print "Do nothing. Kitchen sonos is already playing."
    else:
    #   If controller is not playing, ungroup and start KITCHEN
      track = random.randrange(0, (len(kitchen_sonos.get_queue()) -1))
      print("Controller is not playing, ungroup and start KITCHEN playing random track %d" % track)
      kitchen_sonos.unjoin()
      kitchen_sonos.play_from_queue(track)

  # Sleep for a couple of seconds to prevent rapid stop/starts confusing things
  time.sleep(2)

def sonos_stop():
  # If KITCHEN and LIVINGROOM are both controller, that means the speakers are UNGROUPED
  # Just stop the kitchen sonos.
  if livingroom_sonos.is_coordinator and kitchen_sonos.is_coordinator:
    print "Speakers are ungrouped. Stopping the kitchen."
    kitchen_sonos.stop()
    kitchen_sonos.clear_queue()
  else:
    # If the speakers are grouped, ungroup the kitchen sonos
    print "Speakers are grouped. Stopping just the kitchen"
    kitchen_sonos.unjoin()
    if kitchen_sonos.is_coordinator:
      kitchen_sonos.stop()
  # Sleep for a couple of seconds to prevent rapid stop/starts confusing things
  time.sleep(2)


while True:
    time.sleep(1)
    previous_state = current_state
    current_state = GPIO.input(sensor)

    if current_state != previous_state:
        new_state = "HIGH" if current_state else "LOW"
        #print("GPIO pin %s is %s" % (sensor, new_state))

        if current_state:
          # START PLAYING SONOS
          if sonos_playing == False:
            print "Someones in the kitchen. STARTING SONOS"
            hour = datetime.datetime.now().hour
            print ("Hour %d" % hour)
            if (hour > 22 or hour < 7):
              time.sleep(300)
            else:
              sonos_start()
              sonos_playing = True
              timer=1

        else:
          # START TIMER
          timer=1

    # If the timer has been started, keep timing
    if timer > 0:
      timer=timer+1

    if current_state == False:
      # Check timer. If > 1 min, stop the Sonos and stop the timer.
      if timer > 60:
        print "Nobody detected in the kitchen. STOPPING SONOS"
        sonos_stop()
        sonos_playing = False
        timer = 0

