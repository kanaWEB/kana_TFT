#!/usr/bin/python
# TFT interface that executes commands it is based on Adafruit Camera interface
# This must run as root (sudo python kana_tft.py) due to framebuffer, etc.
#
# Adafruit invests time and resources providing this open source code, 
# please support Adafruit and open-source development by purchasing 
# products from Adafruit, thanks!
#
# http://www.adafruit.com/products/998  (Raspberry Pi Model B)
# http://www.adafruit.com/products/1601 (PiTFT Mini Kit)
# This can also work with the Model A board.
#
# Forked by Remi Sarrailh (madnerds)
# Originally written by Phil Burgess / Paint Your Dragon for Adafruit Industries.
# BSD license, all text above must be included in any redistribution.

import errno
import fnmatch
import io
import os
import os.path
import pygame
import stat
import threading
import time
import ConfigParser
import sched
import sys

from pygame.locals import *
from subprocess import call  

from lib import UI
from lib import Config

# UI callbacks -------------------------------------------------------------
# These are defined before globals because they're referenced by items in
# the global buttons[] list.

def objectCallback(n): # Pass 1 (next setting) or -1 (prev setting)
	global screenMode
	screenMode += n
	if screenMode == -1:
		screenMode = len(buttons) - 1
	elif screenMode == len(buttons): 
		print "set to 0"
		screenMode = 0
	print str(screenMode) + "/" + str(len(buttons) - 1)

def goToCommandCallback():
	global clock,backlight_timer
	clock = False
	backlight_timer = 0
	print "Go to commands"
	print "Drawing Commands"

	img = None         # You get nothing, good day sir
	screen.fill((255,255,255))
	for i,b in enumerate(buttons[screenMode]):
		b.draw(screen)
	pygame.display.update()

def goToClockCallback(): # Exit settings
	global clock,clock_refresh_thread
	global backlight_timer,backlight_timeout,backlight_state
	backlight_state = True
	backlight_timer = 0
	clock = True
	print "Go to clock"
	print "Drawing Clock"

	img = None         # You get nothing, good day sir
	screen.fill((0,0,0))
	for i,b in enumerate(clock_buttons[0]):
		b.draw(screen)
	pygame.display.update()
	clock_refresh_thread = threading.Thread(target=display_time)
	clock_refresh_thread.start()
	
def display_time(): 
	global clock,backlight_timer,backlight_state
	while(clock):
		print backlight_state
		actual_time = time.strftime('%H:%M:%S')
		actual_date = time.strftime("%a, %d %b %Y")
		print actual_time
		print actual_date
		# do your stuff
		label = clock_font_hour.render(actual_time, 1, (255,255,255))
		screen.fill((0,0,0,0), (0,0,320,150))
		screen.blit(label,(32,48))
		
		label = clock_font_date.render(actual_date, 1, (255,255,0))
		screen.blit(label,(30,120))
		pygame.display.update()
		time.sleep(1)
		if (backlight_state == True):
			backlight_timer = backlight_timer + 1
			if(backlight_timer == backlight_timeout):
				backlight(False)

def commandCallback(command,button,screenButton,bg_button):
	command_thread = threading.Thread(target=launchCommand,args=(command,button,screenButton,bg_button,))
	command_thread.start()

def launchCommand(command,button,screenButton,bg_button):
	print "Launch command: "+ command
	active_button(button,screenButton)
	os.system(command)
	unactive_button(button,screenButton,bg_button)

def haltCallback():
	splash_bitmap = pygame.image.load("splash/splash_halt.png")
	screen.blit(splash_bitmap,(0,0))
	pygame.display.update()
	print "Halt"
	os.system("halt")

def rebootCallback():
	splash_bitmap = pygame.image.load("splash/splash_restart.png")
	screen.blit(splash_bitmap,(0,0))
	pygame.display.update()
	print "Reboot"
	os.system("reboot")

def backlight(state):
	global backlight_timer,backlight_state
	backlight_timer = 0
	os.system("echo 252 > /sys/class/gpio/export")
	os.system("echo \'out\' > /sys/class/gpio/gpio252/direction")
	if(state == False):
		backlight_state = False
		print "Backlight OFF"
		os.system("echo '0' > /sys/class/gpio/gpio252/value")
	if(state == True):
		print "Backlight ON"
		backlight_state = True
		os.system("echo '1' > /sys/class/gpio/gpio252/value")

# Global stuff -------------------------------------------------------------

screenMode      =  0      # Current screen mode; default = viewfinder
screenModePrior = -1      # Prior screen mode (for detecting changes)
global clock
clock           =  False  # Last-used settings mode (default = storage)
global backlight_timeout
backlight_timeout = 300
global backlight_state
backlight_state = True
iconPath        = 'icons' # Subdirectory containing UI bitmaps (PNG format)
config_filename = 'config.ini'
icons = [] # This list gets populated at startup

# buttons[] is a list of lists; each top-level list element corresponds
# to one screen mode (e.g. viewfinder, image playback, storage settings),
# and each element within those lists corresponds to one UI button.
# There's a little bit of repetition (e.g. prev/next buttons are
# declared for each settings screen, rather than a single reusable
# set); trying to reuse those few elements just made for an ugly
# tangle of code elsewhere.

config_file = ConfigParser.ConfigParser()
config_file.readfp(open(config_filename))

config = Config.Main(config_file)

id_view = 0
views = []
backlight(True)
while(True):
	try:
		views.append(Config.View(config_file,id_view))
		id_view = id_view + 1
	except ConfigParser.NoSectionError:
		print "-------- No More views"
		break

buttons = []
clock_buttons = []

for v in views:
	buttons.append(
		[
		UI.Button((  0,188,320, 52), bg='clock', cb=goToClockCallback),
		UI.Button((  0,  0, 80, 52), bg='prev', cb=objectCallback, value=-1),
		UI.Button((240,  0, 80, 52), bg='next', cb=objectCallback, value= 1),
		UI.Button((  90, 11,320, 29), text=v.name),
		UI.Button((  48, 60,100,120), bg='button_green', fg='on',cb=commandCallback, button=4, screenButton=len(buttons),value=v.command_on),
		UI.Button((160, 60,100,120), bg='button_red', fg='on',cb=commandCallback, button=5, screenButton=len(buttons),value=v.command_off)
		])

buttons.append(
	[
	UI.Button((  0,188,320, 52), bg='clock'   , cb=goToClockCallback),
	UI.Button((  0,  0, 80, 52), bg='prev'   , cb=objectCallback, value=-1),
	UI.Button((240,  0, 80, 52), bg='next'   , cb=objectCallback, value= 1),
	UI.Button((  48, 60,100,120), bg='quit-reboot', cb=rebootCallback),
	UI.Button((160, 60,100,120), bg='quit-halt', cb=haltCallback),
	UI.Button((  0, 10,320, 35), bg='quit')
	])

clock_buttons.append(
	[
	UI.Button((  0,188,320, 52), bg='commands'   , cb=goToCommandCallback)
	])

# Busy indicator.  To use, run in separate thread, set global 'busy'
# to False when done.
def active_button(i,screenButton):
	buttons[screenButton][i].setBg('button_orange')
	buttons[screenButton][i].draw(screen)
	pygame.display.update()

def unactive_button(i,screenButton,bg_button):
	buttons[screenButton][i].setBg(bg_button)
	buttons[screenButton][i].draw(screen)
	pygame.display.update()
   

# Initialization -----------------------------------------------------------

# Init framebuffer/touchscreen environment variables
os.putenv('SDL_VIDEODRIVER', 'fbcon')
os.putenv('SDL_FBDEV'      , '/dev/fb1')
os.putenv('SDL_MOUSEDRV'   , 'TSLIB')
os.putenv('SDL_MOUSEDEV'   , '/dev/input/touchscreen')

# Init pygame and screen
pygame.init()
pygame.mouse.set_visible(False)
screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)

# Load all icons at startup.
for file in os.listdir(iconPath):
  if fnmatch.fnmatch(file, '*.png'):
	icons.append(UI.Icon(file.split('.')[0]))

# Assign Icons to Buttons, now that they're loaded
for s in buttons:        # For each screenful of buttons...
  for b in s:            #  For each button on screen...
	for i in icons:      #   For each icon...
	  if b.bg == i.name: #    Compare names; match?
		b.iconBg = i     #     Assign Icon to Button
		b.bg     = None  #     Name no longer used; allow garbage collection
	  if b.fg == i.name:
		b.iconFg = i
		b.fg     = None

# Assign Icons to Buttons, now that they're loaded
for s in clock_buttons:        # For each screenful of buttons...
  for b in s:            #  For each button on screen...
	for i in icons:      #   For each icon...
	  if b.bg == i.name: #    Compare names; match?
		b.iconBg = i     #     Assign Icon to Button
		b.bg     = None  #     Name no longer used; allow garbage collection
	  if b.fg == i.name:
		b.iconFg = i
		b.fg     = None

#Label for clock
clock_font_hour = pygame.font.SysFont("arial", 64)
clock_font_date = pygame.font.SysFont("arial", 32)
scheduler = sched.scheduler(time.time, time.sleep)

# Main loop ----------------------------------------------------------------
try:
	while(True):
  	# Process touchscreen input
  		while True:
			for event in pygame.event.get():
				if(event.type is MOUSEBUTTONDOWN):
					pos = pygame.mouse.get_pos()
					if(clock == False):
						for b in buttons[screenMode]:
							if b.selected(pos): break
					elif(clock == True):
						backlight(True)
						for b in clock_buttons[0]:
							if b.selected(pos): break

			# If in viewfinder or settings modes, stop processing touchscreen
			# and refresh the display to show the live preview.  In other modes
			# (image playback, etc.), stop and refresh the screen only when
			# screenMode changes.
			if screenMode != screenModePrior: break

  		img = None         # You get nothing, good day sir
  		screen.fill((255,255,255))

 		 # Overlay buttons on display and update
  		print "Drawing Command"
  		for i,b in enumerate(buttons[screenMode]):
			b.draw(screen)

  		pygame.display.update()

 	 	screenModePrior = screenMode
except KeyboardInterrupt:
	print "Quitting program"
	if(clock == True):
		clock = False
	pygame.quit()
	sys.exit()