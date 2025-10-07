import xbmc, xbmcgui, xbmcaddon, xbmcplugin, xbmcgui
import urllib.request
import os

addon = xbmcaddon.Addon()
addonname = addon.getAddonInfo('name')

url = "https://www.dropbox.com/scl/fi/90rsb9oal9dc3fp3g1l8s/dab19.zip?rlkey=5st59x4bq5xpvljnf0rlflu1z&st=vbsb6tda&dl=1"
path = xbmc.translatePath('special://home/addons/packages/')
zip_file = os.path.join(path, 'dab19.zip')

xbmcgui.Dialog().notification(addonname, 'Downloading Encore build...', xbmcgui.NOTIFICATION_INFO, 5000)

urllib.request.urlretrieve(url, zip_file)

xbmcgui.Dialog().ok('Encore Wizard', f'Download complete:\n{zip_file}')



