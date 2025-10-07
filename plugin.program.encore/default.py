# -*- coding: utf-8 -*-
import xbmc
import xbmcgui
import xbmcaddon
import os
import zipfile
import urllib.request
import shutil

# === BUILD SETTINGS ===
BUILD_NAME = "dab19"
BUILD_VERSION = "1.0.0"
BUILD_ZIP_URL = "https://www.dropbox.com/scl/fi/90rsb9oal9dc3fp3g1l8s/dab19.zip?rlkey=5st59x4bq5xpvljnf0rlflu1z&st=pdnur39y&dl=1"  # direct link
EXTRACT_PATH = "special://home/"
CLEAR_CACHE = True
CLEAR_THUMBNAILS = True

# === ADDON INFO ===
ADDON = xbmcaddon.Addon()
TEMP_ZIP = os.path.join(xbmc.translatePath('special://home/addons/packages/'), 'build.zip')


# === DOWNLOAD FUNCTION ===
def download_file(url, destination):
    try:
        dp = xbmcgui.DialogProgress()
        dp.create("Downloading", "Fetching build package...")

        with urllib.request.urlopen(url) as response, open(destination, 'wb') as out_file:
            file_size = int(response.getheader('Content-Length', 0))
            block_size = 8192
            downloaded = 0

            while True:
                buffer = response.read(block_size)
                if not buffer:
                    break
                downloaded += len(buffer)
                out_file.write(buffer)
                percent = int(downloaded * 100 / file_size)
                dp.update(percent, f"Downloading... {percent}%")

                if dp.iscanceled():
                    dp.close()
                    return False
        dp.close()
        return True
    except Exception as e:
        xbmcgui.Dialog().notification("Download Failed", str(e), xbmcgui.NOTIFICATION_ERROR, 5000)
        return False


# === EXTRACT FUNCTION ===
def extract_zip(zip_path, extract_to):
    try:
        dp = xbmcgui.DialogProgress()
        dp.create("Extracting", "Installing build...")

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            total_files = len(zip_ref.infolist())
            for count, file in enumerate(zip_ref.infolist(), start=1):
                zip_ref.extract(file, extract_to)
                percent = int(count * 100 / total_files)
                dp.update(percent, f"Installing... {percent}%")
                if dp.iscanceled():
                    dp.close()
                    return False
        dp.close()
        return True
    except Exception as e:
        xbmcgui.Dialog().notification("Extraction Failed", str(e), xbmcgui.NOTIFICATION_ERROR, 5000)
        return False


# === INSTALL FUNCTION ===
def install_build():
    confirm = xbmcgui.Dialog().yesno("Confirm Install",
                                     f"Install {BUILD_NAME} v{BUILD_VERSION}?",
                                     nolabel="Cancel", yeslabel="Install")
    if not confirm:
        return

    xbmcgui.Dialog().notification("Starting", f"Installing {dab19}...", xbmcgui.NOTIFICATION_INFO, 3000)

    # Download build ZIP
    if not download_file(BUILD_ZIP_URL, TEMP_ZIP):
        return

    # Clear cache/thumbnails if enabled
    if CLEAR_CACHE:
        cache_path = xbmc.translatePath('special://home/cache')
        shutil.rmtree(cache_path, ignore_errors=True)
    if CLEAR_THUMBNAILS:
        thumbs_path = xbmc.translatePath('special://home/userdata/Thumbnails')
        shutil.rmtree(thumbs_path, ignore_errors=True)

    # Extract ZIP
    if not extract_zip(TEMP_ZIP, xbmc.translatePath(EXTRACT_PATH)):
        return

    # Clean up
    try:
        os.remove(TEMP_ZIP)
    except:
        pass

    xbmcgui.Dialog().ok("Build Installed", f"{dab19} v{1.0.0} installed successfully!")
    xbmcgui.Dialog().notification("Done", "Restart Kodi to load your new build!", xbmcgui.NOTIFICATION_INFO, 5000)


# === ENTRY POINT ===
if __name__ == '__main__':
    install_build()

