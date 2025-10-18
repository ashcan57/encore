# wizard.py — Encore Wizard
if os.path.exists(EXTRACT_DIR):
shutil.rmtree(EXTRACT_DIR)
except Exception:
pass




def main():
# Confirm
if not confirm_full_install():
return


# Backup
xbmc.log('EncoreWizard: creating backup...')
backup_path = make_backup()
if backup_path:
xbmc.log('EncoreWizard: backup at %s' % backup_path)
else:
xbmc.log('EncoreWizard: backup not available')


# Download
ok = download_build(BUILD_URL, DOWNLOAD_PATH)
if not ok:
return


# Extract
xbmc.log('EncoreWizard: extracting...')
ok = safe_extract(DOWNLOAD_PATH, EXTRACT_DIR)
if not ok:
DIALOG.ok('Encore Wizard', 'Failed to extract build')
cleanup()
return


# Copy into HOME
xbmc.log('EncoreWizard: installing build...')
copy_tree(EXTRACT_DIR, HOME)


cleanup()


# Finalize
DIALOG.ok('Encore Wizard', 'Install complete. Kodi will now restart to apply changes.')
xbmc.executebuiltin('RestartApp')




if __name__ == '__main__':
try:
main()
except Exception as e:
xbmc.log('EncoreWizard: unexpected error: %s' % repr(e))
DIALOG.ok('Encore Wizard', 'An unexpected error occurred: %s' % repr(e))