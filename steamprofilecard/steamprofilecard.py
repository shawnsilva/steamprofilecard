#!/usr/bin/env python
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Copyright (C) 2011-2015  Shawn Silva
# ------------------------------------
# This file is part of SteamProfileCard
#
# SteamProfileCard is free software: you can redistribute it and/or modify
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
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
import sys

PYMAJORVER, PYMINORVER, PYMICROVER, PYRELEASELEVEL, PYSERIAL = sys.version_info
if PYMAJORVER == 3 and PYMINORVER >= 2:
    #Python >= 3.2
    from urllib.request import urlopen
elif PYMAJORVER == 2 and PYMINORVER == 7:
    #Python 2.7
    from urllib2 import urlopen
elif PYMAJORVER == 2 and PYMINORVER == 6:
    #Python 2.6
    from urllib2 import urlopen
else:
    raise RuntimeError("Python Version 2.6 or greater required.")

import io, re, os
from datetime import datetime
import xml.etree.ElementTree as ET
from PIL import Image, ImageFont, ImageDraw, ImageChops

from steamwebapi import profiles

TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")

FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")

fontlarge = ImageFont.truetype(os.path.join(FONT_PATH, "FreeSansBold.ttf"), 12, encoding="unic")
font = ImageFont.truetype(os.path.join(FONT_PATH, "FreeSansBold.ttf"), 8, encoding="unic")
sl_font = ImageFont.truetype(os.path.join(FONT_PATH, "slkscr.ttf"), 15, encoding="unic")

def trim(im):
    bg = Image.new(im.mode, im.size, im.getpixel((0,0)))
    diff = ImageChops.difference(im, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()
    if bbox:
        return im.crop(bbox)

class SteamProfileCard:
    def __init__(self, steamuserid, imgtype, template):
        self.steamuserid = steamuserid
        self.imgtype = self.__profileImgType(imgtype)
        self.template = template
        self.profileGrabStatus = True
        try:
            self.user_profile = profiles.get_user_profile(steamuserid)
            if self.user_profile.primaryclanid:
                # Group ID '103582791429521408' is often encountered.
                # In hex, that ID is '0x170000000000000' which has 0 in the 
                # lower 32bits. There is no actual group ID, just the universe,
                # account type identifiers, and the instance.
                # https://developer.valvesoftware.com/wiki/SteamID
                if (int(self.user_profile.primaryclanid) & 0x00000000FFFFFFFF) != 0:
                    self.primary_group_profile = profiles.get_group_profile(self.user_profile.primaryclanid)
                else:
                    self.primary_group_profile = None
            else:
                self.primary_group_profile = None
        except:
            self.profileGrabStatus = False

    def __get_2wk_playtime(self):
        """
        Adds up playtime in each of the games in user_profile.recentlyplayedgames
        and returns the total.
        """
        games = self.user_profile.recentlyplayedgames
        minutes = 0
        for game in games:
            minutes += game['playtime_2weeks']
        return ((minutes + 60 // 2) // 60)
    
    def __profileImgType(self, imgtype):
        """
        Will make sure the imgtype is either "card" or "sig". Will default to "card" if not.
        Returns the type.
        """
        if imgtype == "card":
            self.imgsize = (210, 150)
            return imgtype
        elif imgtype == "sig":
            self.imgsize = (350, 50)
            return imgtype
        else:
            imgtype = "card"
            self.imgsize = (210, 150)
            return imgtype

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

    def __drawSteamLevel(self, steam_level):
        """
        Creates a small circle with the users steam level
        """
        image = Image.new("RGBA", (101,101), color=(255, 255, 255, 0))
        draw = ImageDraw.Draw(image)
        draw.ellipse((0, 0, 100, 100), fill="#00FF00", outline=(255, 255, 255, 0))
        draw.ellipse((5, 5, 95, 95), fill=(255, 255, 255, 0), outline=(255, 255, 255, 0))
        circle = image.resize((35,35), Image.ANTIALIAS)

        # Attempting to center text directly will often be a few pixels off
        # in any direction due to how most fonts have varying heights for
        # characters. ImageFont.getsize doesn't return the actual height of
        # the 'visible' printed characters, but includes whitespace from the 
        # font. To get around this, the text is written on a separate image and
        # then that image is trimmed of all the empty space. This gets the
        # correct width and height of the 'visible' text.
        w, h = sl_font.getsize(steam_level)

        text_img = Image.new("RGBA", (35,35), color=(255, 255, 255, 0))
        text_draw = ImageDraw.Draw(text_img)
        text_draw.text(((35-w)/2,(35-h)/2), steam_level, fill='#FFFFFF', font=sl_font)
        text_trim = trim(text_img)

        w, h = text_trim.size

        circle.paste(text_trim, (int((35-w)/2),int((35-h)/2)) , text_trim)
        return circle

    def __loadBaseTemplateImg(self, template):
        """
        Will load the base template for the profile card based on input. If the
        template can't be found a blank image will be used. If the type of card isn't
        valid (card|sig) the "card" type will be used. Returns a PIL image object.
        """
        imageloaded = False
        templatefile = os.path.join(TEMPLATE_PATH, self.imgtype, template + ".png")
        if os.path.isfile(templatefile):
            try:
                with open(templatefile, 'rb') as f:
                    image = Image.open(f).convert("RGB")
                    if image.size == self.imgsize:
                        imageloaded = True
            except:
                pass
        if imageloaded == False:
            image = Image.new("RGB", self.imgsize, color="#808080")
        return image
        
    def __publicProfileCardDraw(self):
        """
        Draws a new profile "card" type with PIL based on Steam User Info. Returns a PIL image object.
        """
        image = self.__loadBaseTemplateImg(self.template)
        draw = ImageDraw.Draw(image)
        
        
        draw.text((78,35), self.user_profile.personaname, font=fontlarge)
        txttowrt = "Joined: %s"  % (datetime.utcfromtimestamp(int(self.user_profile.timecreated)).strftime('%B %d, %Y'))
        draw.text((70,52), txttowrt, font=font)
        txttowrt = "Steam Level: %s" % (self.user_profile.steamlevel)
        draw.text((70,62), txttowrt, font=font)
        txttowrt = "Played: %s hrs past 2 weeks" % (self.__get_2wk_playtime())
        draw.text((70,72), txttowrt, font=font)

        if self.user_profile.personastate in ['Online', 'Looking to Trade', 'Looking to Play']:
            statusimage = self.__onlineStateDraw("#00FF00")
        elif self.user_profile.personastate in ['Away', 'Snooze']:
            statusimage = self.__onlineStateDraw("#FF9933")
        elif self.user_profile.personastate in ['Busy']:
            statusimage = self.__onlineStateDraw("#FF0000")
        else:
            statusimage = self.__onlineStateDraw("#A3A3A3")
        image.paste(statusimage, (70, 40), statusimage)
        
        steam_level_image = self.__drawSteamLevel(str(self.user_profile.steamlevel))
        image.paste(steam_level_image, (165, 10), steam_level_image)
        
        try:
            avatarIM = Image.open(io.BytesIO(urlopen(self.user_profile.avatarmedium).read())).resize((55,55), Image.ANTIALIAS)
            image.paste(avatarIM, (10,35))
        except:
            pass
        
        if self.primary_group_profile:
            try:
                groupIM = Image.open(io.BytesIO(urlopen(self.primary_group_profile.avataricon).read())).resize((20, 20), Image.ANTIALIAS)
                image.paste(groupIM, (10,5))
            except:
                pass
            txttowrt = "\"%s\" Member" % (self.primary_group_profile.groupname)
            draw.text((10, 90), txttowrt, font=font)
            if self.user_profile.profileurlname:
                draw.text((35,7), self.user_profile.profileurlname, font=fontlarge)
        else:
            if self.user_profile.profileurlname:
                draw.text((10,7), self.user_profile.profileurlname, font=fontlarge)
            
        if len(self.user_profile.recentlyplayedgames) > 0:
            try:
                firstgameIM = Image.open(io.BytesIO(urlopen(self.user_profile.recentlyplayedgames[0]['img_icon_url']).read()))
                image.paste(firstgameIM, (10,112))
            except:
                pass
            txttowrt = (self.user_profile.recentlyplayedgames[0]['name'][:22] + "...") if len(self.user_profile.recentlyplayedgames[0]['name']) > 22 else self.user_profile.recentlyplayedgames[0]['name']
            draw.text((45, 112), txttowrt, font=font)
            txttowrt = "%s hours" % ((self.user_profile.recentlyplayedgames[0]['playtime_2weeks']+60//2)//60)
            draw.text((45,122), txttowrt, font=font)
            xoffset = 138

            for game in self.user_profile.recentlyplayedgames[1:3]:
                try:
                    gameIcon = Image.open(io.BytesIO(urlopen(game['img_icon_url']).read()))
                    image.paste(gameIcon, (xoffset,112))
                    xoffset = xoffset + 35
                except:
                    pass
                

        return image
    
    def __publicProfileSigDraw(self):
        """
        Draws a new profile "sig" type with PIL based on Steam User Info. Returns a PIL image object.
        """
        image = self.__loadBaseTemplateImg(self.template)
        draw = ImageDraw.Draw(image)
        
        try:
            avatarIM = Image.open(io.BytesIO(urlopen(self.user_profile.avatarmedium).read())).resize((40,40), Image.ANTIALIAS)
            image.paste(avatarIM, (5,5))
        except:
            pass
        
        if self.user_profile.personastate == "Online" or self.user_profile.personastate == "Snooze":
            statusimage = self.__onlineStateDraw("#00FF00")
        else:
            statusimage = self.__onlineStateDraw("#FF0000")
        
        
        if self.primary_group_profile:
            try:
                groupIM = Image.open(io.BytesIO(urlopen(self.primary_group_profile.avataricon).read())).resize((20, 20), Image.ANTIALIAS)
                image.paste(groupIM, (57,2))
            except:
                pass
            image.paste(statusimage, (82, 9), statusimage)
            draw.text((90,4), self.user_profile.personaname, font=fontlarge)
        else:
            image.paste(statusimage, (57, 9), statusimage)
            draw.text((65,4), self.user_profile.personaname, font=fontlarge)
        
        txttowrt = "Steam Level: %s" % (self.user_profile.steamlevel)
        draw.text((57,35), txttowrt, font=font)
        
        txttowrt = "Played: %s hrs past 2 weeks" % (self.__get_2wk_playtime())
        draw.text((57,25), txttowrt, font=font)

        # This doesn't look very good, and the entire sig needs to have a 
        # new layout.
        # steam_level_image = self.__drawSteamLevel(str(self.user_profile.steamlevel))
        # image.paste(steam_level_image, (175, 7), steam_level_image)

        xoffset = 325
        for game in reversed(self.user_profile.recentlyplayedgames[:5]):
            try:
                gameIcon = Image.open(io.BytesIO(urlopen(game['img_icon_url']).read())).resize((20, 20), Image.ANTIALIAS)
                image.paste(gameIcon, (xoffset,25))
                xoffset = xoffset - 25
            except:
                pass
            
        
        return image
    
    def __profileErrorDraw(self, error):
        """
        If there was an error retrieving Steam user info this will draw an image to report the error.
        Returns a PIL image object.
        """
        image = Image.new("RGB", self.imgsize)
        draw = ImageDraw.Draw(image)
        draw.text((10,10), "The Steam profile for custom URL: ", font=font)
        draw.text((20,20), self.steamuserid, font=font)
        draw.text((10,30), error, font=font)
        return image
    
    def drawProfileImg(self):
        """
        After the class is initialized this function can be called to draw an image. If any errors
        were found in obtaining user info it will draw an error image, otherwise a profile card|sig is generated.
        Returns a PIL image object.
        """
        if self.profileGrabStatus == False:
            self.profileImage = self.__profileErrorDraw("had an error retrieving xml")
        elif not self.user_profile.communityvisibilitystate == "Private":
            if self.imgtype == "card":
                self.profileImage = self.__publicProfileCardDraw()
            elif self.imgtype == "sig":
                self.profileImage = self.__publicProfileSigDraw()
        elif self.user_profile.personaname:
            self.profileImage = self.__profileErrorDraw("is not public.")
        else:
            self.profileImage = self.__profileErrorDraw("doesn't exist.")
        return self.profileImage
    
    def imageToWeb(self):
        """
        Will attempt to save the generated PIL image object as a PNG stream so it can be include in web output.
        """
        self.imgStream = io.BytesIO()
        try:
            self.profileImage.save(self.imgStream, "PNG")
        except:
            return False
        self.imgStream.seek(0)
        return self.imgStream.read()

def main():
    card = SteamProfileCard("vanityURL", "card", "default")
    profileImg = card.drawProfileImg()
    profileImg.show()

if __name__ == "__main__":
    main()
