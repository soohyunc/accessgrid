#!/usr/bin/python
# A globally unique identifier made up of time and ip
# Copyright (C) 2002  Dr. Conan C. Albrecht <conan_albrecht@byu.edu>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307	USA

import random
import socket
import time

class GUID:
  '''
  A globally-unique identifier made up of time and ip and 3 random
  digits: 35 characters wide A globally unique identifier that
  combines ip, time, and random bits.  Since the time is listed first,
  you can sort records by guid.  You can also extract the time and ip
  if needed.

  GUIDs make wonderful database keys.  They require no access to the
  database (to get the max index number), they are extremely unique,
  and they sort automatically by time.  GUIDs prevent key clashes when
  merging two databases together, combining data, or generating keys
  in distributed systems.
  '''
  rand = random.Random(time.time())
  ip = ''
  try:
    ip = socket.gethostbyname(socket.gethostname())
    # if we don't have an ip, default to someting in the 10.x.x.x private range
  except (socket.gaierror): 
    ip = '10'
    for i in range(3):
      ip += '.' + str(rand.randrange(1, 254))
  # leave space for ip v6 (65K in each sub)
  hexip = ''.join(["%04x" % long(i) for i in ip.split('.')]) 
  lastguid = ''

  def __init__(self, guid=None):
    ''' Constructor.  Use no args if you want the guid generated (this is
    the normal method) or send a string-typed guid to generate it from
    the string'''
    if guid == None:
      self.guid = self.__class__.lastguid
      while self.guid == self.__class__.lastguid:
	# time part
	now = long(time.time() * 1000)
	self.guid = ("%016x" % now) + self.__class__.hexip
	# random part
	self.guid += ("%03x" % (self.__class__.rand.randrange(0, 4095)))
      self.__class__.lastguid = self.guid

    elif type(guid) == type(self): # if a GUID object, copy its value
      self.guid = str(guid)

    else: # if a string, just save its value
      self.guid = guid

  def __str__(self):
    '''Returns the string value of this guid'''
    return self.guid

  def time(self):
    '''Extracts the time portion out of the guid and returns the 
      number of milliseconds since the epoch'''
    return long(self.guid[0:16], 16)

  def ip(self):
    '''Extracts the ip portion out of the guid and returns it
      as a string like 10.10.10.10'''
    # there's probably a more elegant way to do this
    ip = ''
    index = 16
    while index < 32:
      if ip != '':
	ip += "."
      ip += str(int(self.guid[index: index + 4], 16))
      index += 4
    return ip

  def random(self):
    ''' Extracts the random bits from the guid. I have no idea how this
    would be useful, but I've included it for completeness. '''
    return int(self.guid[-3:], 16)

if __name__ == "__main__":
  # just print out a for testing
  guid = GUID()
  print "GUID: " + str(guid)
  millis = guid.time()
  print "Time: " + str(millis) + " millis (" + time.asctime(time.gmtime(millis / 1000)) + " UTC)"
  print "IP:   " + guid.ip()
  print "Rand: " + str(guid.random()) 





