#!/usr/bin/python
import ConfigParser, os

class Main:
	def __init__(self,config_file):
		print "Main configuration is not implemented yet"
		#self.lang = config_file.get("config","lang")
		#self.default_view = config_file.get("config","default_view")
		#print "Language:"+self.lang
		#print "Default_view:"+self.default_view

class View:
	def __init__(self,config_file,id_view):	
		self.name = config_file.get("view"+str(id_view),"name")
		print "Getting all view"
		print "-------- View"+str(id_view)
		self.command_on = config_file.get("view"+str(id_view),"command_on")
		self.command_off = config_file.get("view"+str(id_view),"command_off")
