from jurialmunkey.ftools import cached_property
from tmdbhelper.lib.addon.consts import HALFDAY_EXPIRY
from tmdbhelper.lib.addon.tmdate import set_timestamp
from tmdbhelper.lib.sync.datatype import timerlock
from tmdbhelper_sync_trakt.sync.datatype import TraktDataType, TraktDataTypeEpisodesInShows, TraktDataTypeShowsToEpisodes


class SyncHiddenProgressWatched(TraktDataType):
    keys = ('hidden_at', )
    last_activities_key = 'hidden_at'
    method = 'hidden/progress_watched'
    key_prefix = 'progress_watched'

    @timerlock
    def sync_func(self):
        """ Get items that are hidden on Trakt """
        from tmdbhelper.lib.addon.logger import TimerFunc
        with TimerFunc(f'Sync: {self.__class__.__name__} get_response_sync users {self.method} {self.item_type}', inline=True, log_threshold=0.001):
            return self.get_response_sync(
                'users', self.method,
                type=f'{self.item_type}s'
            )


class SyncHiddenProgressCollected(SyncHiddenProgressWatched):
    last_activities_key = 'hidden_at'
    method = 'hidden/progress_collected'
    key_prefix = 'progress_collected'


class SyncHiddenCalendar(SyncHiddenProgressWatched):
    last_activities_key = 'hidden_at'
    method = 'hidden/calendar'
    key_prefix = 'calendar'


class SyncHiddenDropped(SyncHiddenProgressWatched):
    last_activities_key = 'dropped_at'
    method = 'hidden/dropped'
    key_prefix = 'dropped'


class SyncWatched(TraktDataTypeEpisodesInShows):
    keys = ('plays', 'last_watched_at', 'last_updated_at', 'aired_episodes', 'watched_episodes', 'reset_at', )
    last_activities_key = 'watched_at'
    sync_kwgs = {'extended': 'full,progress'}
    method = 'watched'


class SyncPlayback(TraktDataTypeShowsToEpisodes):
    keys = ('progress', 'paused_at', 'id', )
    last_activities_key = 'paused_at'
    sync_kwgs = {'extended': 'full'}
    method = 'playback'
    key_prefix = 'playback'


class SyncWatchlist(TraktDataType):
    keys = ('rank', 'listed_at', 'notes', )
    last_activities_key = 'watchlisted_at'
    sync_kwgs = {'extended': 'full'}
    method = 'watchlist'
    key_prefix = 'watchlist'


class SyncCollection(TraktDataTypeEpisodesInShows):
    keys = ('last_collected_at', 'last_updated_at', )
    last_activities_key = 'collected_at'
    method = 'collection'
    key_prefix = 'collection'


class SyncAllNextEpisodes(TraktDataTypeEpisodesInShows):
    keys = ('upnext_episode_id', )
    last_activities_key = 'watched_at'
    method = 'all_next_episodes'

    @cached_property
    def use_airtime(self):
        return self.provider.settings.use_airtime

    @property
    def expiry_time(self):
        return 600 if self.use_airtime else HALFDAY_EXPIRY

    @cached_property
    def airing_configuration(self):
        return f'{int(self.use_airtime)}.{int(self.provider.settings.use_calendar)}'

    @property
    def airing_activity_method(self):
        return f'{self.cache_method}.airing'

    @cached_property
    def is_expired(self):
        return self.get_is_expired()

    def get_is_expired(self):
        # The shared columns contain one calculation, not a separate result per policy.
        configuration = self.cache.get_activity(self.item_type, self.airing_activity_method)
        return configuration != self.airing_configuration or super().is_expired

    def store_last_activity(self):
        super().store_last_activity()
        self.cache.set_activity(
            self.item_type,
            self.airing_activity_method,
            self.airing_configuration,
            set_timestamp(self.expiry_time, set_int=True),
        )

    @timerlock
    def sync_func(self):
        """ Get next episodes on Trakt """
        from tmdbhelper.lib.addon.logger import TimerFunc
        from tmdbhelper_sync_trakt.sync.nextmeta import TraktSyncAllNextEpisodesMeta
        with TimerFunc(
            f'Sync: {self.__class__.__name__} get_meta {self.method} {self.item_type}',
            inline=True,
            log_threshold=0.001
        ):
            return TraktSyncAllNextEpisodesMeta(self).items


class SyncNextEpisodes(SyncAllNextEpisodes):
    keys = ('next_episode_id', 'next_episode_aired_at')
    last_activities_key = 'watched_at'
    method = 'nextup'

    @timerlock
    def sync_func(self):
        """ Get next episodes on Trakt """
        from tmdbhelper.lib.addon.logger import TimerFunc
        from tmdbhelper_sync_trakt.sync.nextmeta import TraktSyncNextEpisodesMeta
        with TimerFunc(
            f'Sync: {self.__class__.__name__} get_meta {self.method} {self.item_type}',
            inline=True,
            log_threshold=0.001
        ):
            return TraktSyncNextEpisodesMeta(self).items
