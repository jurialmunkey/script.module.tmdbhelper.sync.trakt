from os.path import join
from xml.etree import ElementTree
from xbmcaddon import Addon
from xbmcvfs import File, exists, translatePath
from jurialmunkey.window import get_property
from tmdbhelper.lib.files.locker import mutexlock


class TraktSettings:
    addon_id = 'script.module.tmdbhelper.sync.trakt'
    mutex_lockname = 'TraktCheckingAuthorization'
    legacy_settings = {
        'cache_own_lists': 'trakt_cacheownlists',
        'genre_icon_location': 'trakt_genre_icon_location',
        'use_calendar': 'nextepisodes_usecalendar',
    }

    def __init__(self):
        self.addon = Addon(self.addon_id)

    @property
    def cache_own_lists(self):
        return self.addon.getSettingBool('cache_own_lists')

    @property
    def genre_icon_location(self):
        return self.addon.getSetting('genre_icon_location')

    @property
    def use_calendar(self):
        return self.addon.getSettingBool('use_calendar')

    @property
    def use_airtime(self):
        return self.addon.getSettingBool('use_airtime')

    def get_configured_settings(self):
        path = join(translatePath(self.addon.getAddonInfo('profile')), 'settings.xml')
        if not exists(path):
            return frozenset()
        with File(path) as settings_file:
            settings = ElementTree.fromstring(settings_file.read())
        return frozenset(
            setting.get('id') for setting in settings.iter('setting')
            if setting.get('default') != 'true')

    def migrate_setting(self, name, value):
        self.addon.setSetting(name, value)
        if self.addon.getSetting(name) != value:
            raise RuntimeError(f'Unable to save migrated Trakt setting: {name}')

    def migrate_settings(self):
        self.migrate_preferences()
        self.migrate_credentials()

    def migrate_preferences(self):
        if self.addon.getSettingBool('preferences_migrated'):
            return
        configured = self.get_configured_settings()
        legacy_addon = Addon('plugin.video.themoviedb.helper')
        for name, legacy_name in self.legacy_settings.items():
            if name not in configured:
                self.migrate_setting(name, legacy_addon.getSetting(legacy_name))
        self.migrate_setting('preferences_migrated', 'true')

    def migrate_credentials(self):
        if self.addon.getSettingBool('credentials_migrated'):
            return
        if self.migrate_credentials_locked() is not True:
            raise RuntimeError('Trakt credential migration was interrupted')

    @mutexlock
    def migrate_credentials_locked(self):
        if self.addon.getSettingBool('credentials_migrated'):
            return True
        configured = self.get_configured_settings()
        if 'token' not in configured and not self.addon.getSetting('token'):
            legacy_addon = Addon('plugin.video.themoviedb.helper')
            self.migrate_setting('token', legacy_addon.getSetting('trakt_token'))
        self.migrate_setting('credentials_migrated', 'true')
        self.clear_authorization_session()
        return True

    @staticmethod
    def clear_authorization_session():
        for name in (
                'TraktUserToken', 'TraktIsAuth', 'TraktRefreshAttempts',
                'TraktRefreshTimeStamp', 'TraktAttemptedLogin'):
            get_property(name, clear_property=True)
