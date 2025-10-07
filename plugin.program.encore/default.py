# -*- coding: utf-8 -*-
import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin
import os
import zipfile
import urllib.request
import shutil

# Import your build settings
import uservar

# === GET ADDON INFO ===
ADDON = xbmcaddon.Addon()
HOME = xbmc.translatePath(ADDON.getAddonInfo('path'))
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

# === MAIN INSTALLER ===
def install_build():
    confirm = xbmcgui.Dialog().yesno("Confirm Install",
                                     f"Install {uservar.buildname} v{uservar.buildversion}?",
                                     nolabel="Cancel", yeslabel="Install")
    if not confirm:
        return

    xbmcgui.Dialog().notification("Starting", uservar.installmessage, xbmcgui.NOTIFICATION_INFO, 3000)

    # Download build
    if not download_file(uservar.buildzip, TEMP_ZIP):
        return

    # Clear cache if enabled
    if uservar.clearcache:
        cache_path = xbmc.translatePath('special://home/cache')
        if os.path.exists(cache_path):
            shutil.rmtree(cache_path, ignore_errors=True)

    # Extract build
    if not extract_zip(TEMP_ZIP, xbmc.translatePath(uservar.extractpath)):
        return

    # Clean up
    os.remove(TEMP_ZIP)

    xbmcgui.Dialog().ok("Build Installed", uservar.complete_message)

    xbmcgui.Dialog().notification("Done", "Restart Kodi to load your new build!", xbmcgui.NOTIFICATION_INFO, 5000)


# === ENTRY POINT ===
if __name__ == '__main__':
    install_build()


