import sys
import xbmcaddon
import xbmcgui
import xbmc
import requests
import re

def handle_windows_playback(play_item, mpd_mod, custom_data):
    try:
        script_cdm_path = xbmcaddon.Addon('script.windows.playback').getAddonInfo('path')
        if script_cdm_path not in sys.path:
            sys.path.append(script_cdm_path)

        from addon import get_keys
    except Exception as e:
        xbmc.log(f"Failed to import script.windows.playback: {e}", xbmc.LOGERROR)
        xbmcgui.Dialog().ok("Error", "Ez az addon nem lett telepítve: script.windows.playback")
        sys.exit(1)

    def get_clearkey_from_manifest(mpd_url):
        try:
            lic_url = 'https://widevine.keyos.com/api/v4/getLicense'

            mpd_headers = {
                'Accept': '*/*',
                'Accept-Language': 'hu',
                'Connection': 'keep-alive',
                'Origin': 'https://nava.hu',
                'Referer': 'https://nava.hu/',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
            }

            response = requests.get(mpd_url, headers=mpd_headers)
            response.raise_for_status()
            content = response.content.decode('utf-8')

            pssh_pattern = r'<ContentProtection schemeIdUri="urn:uuid:edef8ba9-79d6-4ace-a3c8-27dcd51d21ed".*?>\s*<cenc:pssh>(.*?)</cenc:pssh>'
            pssh_match = re.search(pssh_pattern, content, re.DOTALL)

            if not pssh_match:
                xbmcgui.Dialog().ok("Error", "PSSH nem található.")
                return None, "PSSH nem található."

            lic_headers = {
                'accept': '*/*',
                'accept-language': 'hu',
                'customdata': custom_data,
                'origin': 'https://nava.hu',
                'priority': 'u=1, i',
                'referer': 'https://nava.hu/',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
                'content-type': 'application/x-www-form-urlencoded',
            }

            pssh_text = pssh_match.group(1)
            keys_data = get_keys(pssh_text, lic_url, lic_headers)

            if keys_data.get('error'):
                xbmcgui.Dialog().ok("Error", keys_data['error'])
                return None, keys_data.get('error')

            return keys_data.get('key'), None

        except requests.exceptions.RequestException as e:
            xbmcgui.Dialog().ok("Error", f'Manifest download failed: {e}')
            return None, f'Manifest download failed: {e}'

    clearkey, error_message = get_clearkey_from_manifest(mpd_mod)
    if clearkey:
        play_item.setMimeType('application/dash+xml')
        play_item.setProperty('inputstream', 'inputstream.adaptive')
        play_item.setProperty('inputstream.adaptive.manifest_type', 'mpd')
        play_item.setProperty('inputstream.adaptive.drm_legacy', f'org.w3.clearkey|{clearkey}')
        play_item.setProperty('IsPlayable', 'true')
