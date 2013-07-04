# SteamProfileCard
## README

### Description
Using the Steam Web API this script will make a "gamer card" of a
given Steam Profile and return a PNG image.

This script will take the users steam url/id and use it to gather
their profile information. The info is then turned into an image
in the style of a "gamer card" or signature image for using in forums. 
This can then be returned to output as an image file on a webpage or
saved to disk.

### How to use 
```python
from steamprofilecard import SteamProfileCard
profile = SteamProfileCard("customURLorID", "card", "template")
card = profile.drawProfileCard()
```

or

```python
card.save("/path/to/save/image.png", "PNG")
pngimg = profile.imageToWeb()
```

SteamProfileCard(id, type, template) creates the profile object.
The "id" is your Steam ID or your Steam Custom URL. The "type"
determines if a gamer card or signature will be drawn. The "type"
must be either "card" or "sig". If it is set to an invalid type
a default of "card" will be used. The "template" is the filename 
of the background template to the image without the file extension.

drawProfileCard() will return a Python Imaging Library (PIL) image 
object that can be further modified if desired. Using the PIL 
Image.save(path, format) will allow you to save the image to disk.

Otherwise, imageToWeb() will return the image to a PNG format that 
can be easily output on a website. It should only be used after 
drawProfileCard() has been run. The returned data can be sent to 
a web browser with the Content Type set to image/png. This allows
the script to be called as an image allowing dynamic profile status
to be displayed.

###REQUIREMENTS
* Python
    * 3.3.*
    * 3.2.*
    * 2.7.*
    * 2.6.*
* Pillow (PIL Fork)(http://python-imaging.github.io/)
    * 2.1.0
    * 2.0.0
