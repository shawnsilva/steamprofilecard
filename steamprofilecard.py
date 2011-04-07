#!/usr/bin/python
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# steamprofilecard.py
# Version: 0.1.0
# By: Shawn Silva (shawn at jatgam dot com)
# 
# Created: 4/6/2011
# Modified: 4/6/2011
# 
# Using the Steam Web API this script will make a "gamer card" of a
# given Steam Profile and return a PNG image.
# -----------------------------------------------------------------
# This script will take the users steam url/id and use it to gather
# their profile information. The info is then turned into an image
# in the style of a "gamer card". This can then be returned to output
# as an image file on a webpage.
#
# Example: profile = SteamProfileCard("customURLorID", "card", "template")
#          card = profile.drawProfileCard()
#          pngimg = profile.imageToFile()
#
# drawProfileCard() will return a Python Imaging Library (PIL) image 
# object that can be further modified if desired. Otherwise, 
# imageToFile() will save the image to a PNG format that can be 
# easily output on a website.
# 
# 
# Copyright (C) 2011  Shawn Silva
# -------------------------------
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
#                               TODO                              #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# - Fix font/images size/placement to be more appealing.
# - Change the way fonts are designated to be easily modified.
# - Implement background templates so the image isn't solid black
#   behind the steam information.
# - Handle a "sig" type for thin bands to use in forum signatures
#   as opposed to the larger "card" type.
# 
# 
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#                             CHANGELOG                           #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# 4/6/2011		v0.1.0 - Initial script creation.
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
import urllib2, cStringIO, re
import xml.etree.ElementTree as ET
import ImageFont, ImageDraw
from PIL import Image

class SteamProfileCard:
	def __init__(self, steamuserid, type, template):
		self.steamuserid = steamuserid
		self.type = type
		self.template = template
		self.steampuburl = self.__steamURLType(self.steamuserid)
		self.__steamPublicXMLParse(self.steampuburl)

	def __steamURLType(self, userid):
		"""
		Checks the userid input to see if it is a custom url or steam ID. Returns the corresponding URL string.
		"""
		regex = re.compile('^\d{17}$')
		if regex.match(userid):
			url = "http://steamcommunity.com/profiles/%s/?xml=1" % (userid)
		else:
			url = "http://steamcommunity.com/id/%s/?xml=1" % (userid)
		return url
	
	def __steamPublicXMLParse(self, url):
		"""
		Takes a URL input for Steam Community Profile in XML format. ex: http://steamcommunity.com/id/CustomUrl/?xml=1
		Sets variables for Steam profile information.
		"""
		try:
			pubtree = ET.parse(urllib2.urlopen(url))
			self.profileGrabStatus = True
		except:
			self.profileGrabStatus = False
			return
		self.id64 = pubtree.findtext("steamID64")
		self.id = pubtree.findtext("steamID")
		self.steamcustomurl = pubtree.findtext("customURL")
		self.privacystate = pubtree.findtext("privacyState")
		self.status = pubtree.findtext("onlineState")
		self.avatarURL = pubtree.findtext("avatarMedium")
		self.membersince = pubtree.findtext("memberSince")
		self.steamrating = pubtree.findtext("steamRating")
		self.hoursplayed2wk = pubtree.findtext("hoursPlayed2Wk")
		self.topGamesPlayed = self.__gamesPlayedParse(list(pubtree.iter("mostPlayedGame")))
		self.primarygroup = self.__primaryGroupParse(list(pubtree.iter("group")))
		return

	def __gamesPlayedParse(self, gamelist):
		"""
		Takes a XML object containing a list of games played recently. Returns a list with dictionaires
		for each individual game containing the name, link, icon, hoursplayed, and hoursonrecord.
		"""
		gamesPlayed = []
		for game in gamelist:
			a = {'name': game.findtext("gameName"), 'link': game.findtext("gameLink"), 'icon': game.findtext("gameIcon"), 'hoursplayed': game.findtext("hoursPlayed"), 'hoursonrecord': game.findtext("hoursOnRecord")}
			gamesPlayed.append(a)
		return gamesPlayed

	def __primaryGroupParse(self, grouplist):
		"""
		Takes a XML object with a list of groups and returns a dictionary of the primary group containing
		the name and icon URL.
		"""
		for group in grouplist:
			if group.attrib["isPrimary"] == "1":
				primarygroup = {'name': group.findtext("groupName"), 'icon': group.findtext("avatarIcon")}
				return primarygroup
		return False

	def __steamRatingConvert(self, rating):
		"""
		Takes a number input 0.0 - 10.0 and returns a string representing the Steam rating level.
		"""
		if rating >= 0 and rating < 1:
			return "Teh Suck"
		elif rating >= 1 and rating < 2:
			return "El Terrible!"
		elif rating >= 2 and rating < 3:
			return "Nearly Lifeless"
		elif rating >= 3 and rating < 4:
			return "Shooting Blanks"
		elif rating >= 4 and rating < 5:
			return "Master of Nothing"
		elif rating >= 5 and rating < 6:
			return "Halfway Cool"
		elif rating >= 6 and rating < 7:
			return "Oooh! Shiny!"
		elif rating >= 7 and rating < 8:
			return "Wax on, Wax off"
		elif rating >= 8 and rating < 9:
			return "COBRA KAI!"
		elif rating >= 9 and rating < 10:
			return "Still not 10"
		elif rating == 10:
			return "EAGLES SCREAM!"
		else:
			return "N/A"

	def __publicProfileCardDraw(self):
		"""
		Draws a new image with PIL based on Steam User Info. Returns a PIL image object.
		"""
		image = Image.new("RGB", (210,150))
		draw = ImageDraw.Draw(image)
		#font = ImageFont.load_default()
		font = ImageFont.truetype("c:\FreeMonoBold.ttf", 9, encoding="unic")
		draw.text((30,10), self.steamcustomurl, font=font)
		
		
		draw.text((80,20), self.id, font=font)
		txttowrt = "Joined: %s"  % (self.membersince)
		draw.text((80,30), txttowrt, font=font)
		txttowrt = "Rating: %s %s" % (self.steamrating, self.__steamRatingConvert(float(self.steamrating)))
		draw.text((80,40), txttowrt, font=font)
		txttowrt = "Played: %s hrs past 2 weeks" % (self.hoursplayed2wk)
		draw.text((80,50), txttowrt, font=font)
		
		try:
			avatarIM = Image.open(cStringIO.StringIO(urllib2.urlopen(self.avatarURL).read()))
			image.paste(avatarIM, (10,20))
		except:
			pass
		
		if self.primarygroup:
			try:
				groupIM = Image.open(cStringIO.StringIO(urllib2.urlopen(self.primarygroup['icon']).read())).resize((20, 20))
				image.paste(groupIM, (10,0))
			except:
				pass
			txttowrt = "\"%s\" Member" % (self.primarygroup['name'])
			draw.text((10, 80), txttowrt, font=font)
			
		if len(self.topGamesPlayed) > 0:
			try:
				firstgameIM = Image.open(cStringIO.StringIO(urllib2.urlopen(self.topGamesPlayed[0]['icon']).read()))
				image.paste(firstgameIM, (10,100))
			except:
				pass
			draw.text((50, 100), self.topGamesPlayed[0]['name'], font=font)
			txttowrt = "%s hours" % (self.topGamesPlayed[0]['hoursplayed'])
			draw.text((50,110), txttowrt, font=font)
			xoffset = 160
			for i in range(1,len(self.topGamesPlayed)):
				try:
					gameIcon = Image.open(cStringIO.StringIO(urllib2.urlopen(self.topGamesPlayed[i]['icon']).read()))
					image.paste(gameIcon, (xoffset,100))
				except:
					pass
				xoffset = xoffset - 40

		return image
	
	def __profileErrorDraw(self, error):
		"""
		If there was an error retrieving Steam user info this will draw an image to report the error.
		Returns a PIL image object.
		"""
		image = Image.new("RGB", (210,150))
		draw = ImageDraw.Draw(image)
		font = ImageFont.truetype("c:\FreeMonoBold.ttf", 10, encoding="unic")
		draw.text((10,20), "The Steam profile for custom URL: ", font=font)
		draw.text((20,30), self.steamcustomurl, font=font)
		draw.text((10,40), error, font=font)
		return image
	
	def drawProfileImg(self):
		"""
		After the class is initialized this function can be called to draw an image. If any errors
		were found in obtaining user info it will draw an error image, otherwise a profile card is generated.
		Returns a PIL image object.
		"""
		if self.profileGrabStatus == False:
			self.profileImage = self.__profileErrorDraw("had an error retrieving xml")
		elif self.privacystate == "public":
			self.profileImage = self.__publicProfileCardDraw()
		elif self.id:
			self.profileImage = self.__profileErrorDraw("is not public.")
		else:
			self.profileImage = self.__profileErrorDraw("doesn't exist.")
		return self.profileImage
	
	def imageToFile(self):
		"""
		Will attempt to save the generated PIL image object as a PNG stream so it can be include in web output.
		"""
		self.imgStream = cStringIO.StringIO()
		try:
			self.profileImage.save(self.imgStream, "PNG")
		except:
			return False
		self.imgStream.seek(0)
		return self.imgStream.read()

def main():
	card = SteamProfileCard("sinkigobopo", "card", "template")
	
	
	profileImg = card.drawProfileImg()
	
	
	profileImg.show()
	#imgStream = cStringIO.StringIO()
	#profileImg.save(imgStream, "PNG")
	#print "Content-type: image/png\n"
	#imgStream.seek(0)
	#print imgStream.read()

if __name__ == "__main__":
	main()