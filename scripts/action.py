#!/usr/bin/python
import urllib2
import sys
url = sys.argv[1]
urllib2.urlopen(url).read()
