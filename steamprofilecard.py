#!/usr/bin/python
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# steamprofilecard.py
# Version: 0.1.4
# By: Shawn Silva (shawn at jatgam dot com)
# 
# Created: 04/06/2011
# Modified: 04/26/2011
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
# - Handle a "sig" type for thin bands to use in forum signatures
#   as opposed to the larger "card" type.
# - Optional Image cache to reduce server load?
# 
# 
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#                             CHANGELOG                           #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# 04/26/2011        v0.1.4 - Truncated long game names.
# 04/21/2011        v0.1.3 - Base templates implemented so background
#                            isn't a solid color.
# 04/20/2011        v0.1.2 - Added Online status indicator.
# 04/11/2011        v0.1.1 - Changed resize filter to improve quality.
#                            Set final alignment for data.
# 04/06/2011        v0.1.0 - Initial script creation.
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
import urllib2, cStringIO, re, os, sys
import xml.etree.ElementTree as ET
import ImageFont, ImageDraw
from PIL import Image

TEMPLATE_PATH = os.path.join(sys.path[0], "templates")
#TEMPLATE_PATH = "/path/to/templates"

FONT_PATH = os.path.join(sys.path[0], "fonts")
#FONT_PATH = "/path/to/fonts"

# CACHE_ENABLED = False			#Image cache to reduce server load.
# CACHE_DURATION = 60			#Time in minutes images are chached for
# CACHE_PATH = "/path/to/cache"	#Path to the folders to store the cahced images.

fontlarge = ImageFont.truetype(os.path.join(FONT_PATH, "FreeSansBold.ttf"), 12, encoding="unic")
font = ImageFont.truetype(os.path.join(FONT_PATH, "FreeSansBold.ttf"), 8, encoding="unic")

class SteamProfileCard:
	def __init__(self, steamuserid, imgtype, template):
		self.steamuserid = steamuserid
		self.imgtype = imgtype
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

	def __onlineStateDraw(self, color):
		"""
		Draws a circle and returns a PIL image 5x5 with the color specified. This is to
		draw a nice smooth circle since PIL can't do it by default.
		"""
		image = Image.new("RGBA", (100,100), color=(255, 255, 255, 0))
		draw = ImageDraw.Draw(image)
		draw.ellipse((0, 0, 100, 100), fill=color, outline="#000000")
		state = image.resize((5,5), Image.ANTIALIAS)
		return state
	
	def __loadBaseTemplateCard(self, template):
		"""
		Will load the base template for the profile card based on input. If the
		template can't be found a blank image will be used. Returns a PIL image object.
		"""
		imageloaded = False
		templatefile = os.path.join(TEMPLATE_PATH, "card", template + ".png")
		if os.path.isfile(templatefile):
			try:
				image = Image.open(templatefile).convert("RGB")
				if image.size == (210, 150):
					imageloaded = True
			except:
				pass
		if imageloaded == False:
			image = Image.new("RGB", (210,150), color="#808080")
		return image
	
	def __publicProfileCardDraw(self):
		"""
		Draws a new image with PIL based on Steam User Info. Returns a PIL image object.
		"""
		image = self.__loadBaseTemplateCard(self.template)
		draw = ImageDraw.Draw(image)
		
		
		draw.text((78,35), self.id, font=fontlarge)
		txttowrt = "Joined: %s"  % (self.membersince)
		draw.text((70,52), txttowrt, font=font)
		txttowrt = "Rating: %s %s" % (self.steamrating, self.__steamRatingConvert(float(self.steamrating)))
		draw.text((70,62), txttowrt, font=font)
		txttowrt = "Played: %s hrs past 2 weeks" % (self.hoursplayed2wk)
		draw.text((70,72), txttowrt, font=font)
		
		if self.status == "online" or self.status == "in-game":
			statusimage = self.__onlineStateDraw("#00FF00")
		else:
			statusimage = self.__onlineStateDraw("#FF0000")
		image.paste(statusimage, (70, 40), statusimage)
		
		
		try:
			avatarIM = Image.open(cStringIO.StringIO(urllib2.urlopen(self.avatarURL).read())).resize((55,55), Image.ANTIALIAS)
			image.paste(avatarIM, (10,35))
		except:
			pass
		
		if self.primarygroup:
			try:
				groupIM = Image.open(cStringIO.StringIO(urllib2.urlopen(self.primarygroup['icon']).read())).resize((20, 20), Image.ANTIALIAS)
				image.paste(groupIM, (10,5))
			except:
				pass
			txttowrt = "\"%s\" Member" % (self.primarygroup['name'])
			draw.text((10, 90), txttowrt, font=font)
			draw.text((35,7), self.steamcustomurl, font=fontlarge)
		else:
			draw.text((10,7), self.steamcustomurl, font=fontlarge)
			
		if len(self.topGamesPlayed) > 0:
			try:
				firstgameIM = Image.open(cStringIO.StringIO(urllib2.urlopen(self.topGamesPlayed[0]['icon']).read()))
				image.paste(firstgameIM, (10,112))
			except:
				pass
			txttowrt = (self.topGamesPlayed[0]['name'][:22] + "...") if len(self.topGamesPlayed[0]['name']) > 22 else self.topGamesPlayed[0]['name']
			draw.text((45, 112), txttowrt, font=font)
			txttowrt = "%s hours" % (self.topGamesPlayed[0]['hoursplayed'])
			draw.text((45,122), txttowrt, font=font)
			xoffset = 168
			for i in range(1,len(self.topGamesPlayed)):
				try:
					gameIcon = Image.open(cStringIO.StringIO(urllib2.urlopen(self.topGamesPlayed[i]['icon']).read()))
					image.paste(gameIcon, (xoffset,112))
				except:
					pass
				xoffset = xoffset - 35

		return image
	
	def __profileErrorDraw(self, error):
		"""
		If there was an error retrieving Steam user info this will draw an image to report the error.
		Returns a PIL image object.
		"""
		image = Image.new("RGB", (210,150))
		draw = ImageDraw.Draw(image)
		draw.text((10,20), "The Steam profile for custom URL: ", font=font)
		draw.text((20,30), self.steamuserid, font=font)
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
	card = SteamProfileCard("sinkigobopo", "card", "default")
	
	
	profileImg = card.drawProfileImg()
	
	
	profileImg.show()


if __name__ == "__main__":
	main()