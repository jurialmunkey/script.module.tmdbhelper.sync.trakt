from jurialmunkey.ftools import cached_property
from tmdbhelper.lib.addon.tmdate import convert_timestamp
from tmdbhelper_sync_trakt.sync.airing import TraktEpisodeAiring
from tmdbhelper.lib.sync.nextmeta import (
    SyncNextEpisodeItem,
    SyncAllNextEpisodesMetaItem,
    SyncAllNextEpisodesMeta,
    SyncNextEpisodesMetaItem,
    SyncNextEpisodesMeta
)


class TraktSyncNextEpisodeItem(SyncNextEpisodeItem):

    @cached_property
    def next_episode_is_unaired(self):
        return self.get_next_episode_is_unaired()

    def get_next_episode_is_unaired(self):
        if not self.main.use_airtime:
            return super().next_episode_is_unaired
        return TraktEpisodeAiring(self.next_episode_aired_at).is_unaired

    @cached_property
    def trakt_slug(self):
        return self.get_trakt_slug()

    def get_trakt_slug(self):
        return self.get_key('trakt_slug')

    def get_id_data(self):
        id_data = super().get_id_data()
        if self.trakt_slug:
            id_data['slug'] = self.trakt_slug
        return id_data

    def is_next_episode(self, season, episode):
        if not episode.get('completed'):
            return True
        if not self.reset_at_datetime_obj:
            return False
        if convert_timestamp(episode.get('last_watched_at')) < self.reset_at_datetime_obj:
            return True
        return False

    @cached_property
    def response(self):
        return self.get_response()

    def get_response(self):
        if not self.trakt_slug:
            return {}
        return self.get_response_sync(
            f'shows/{self.trakt_slug}/progress/watched',
            extended='full',
        )


class TraktSyncAllNextEpisodesMetaItem(SyncAllNextEpisodesMetaItem):
    dialog_progress_bg_text_fstr = '{sync.tmdb_id} {sync.trakt_slug}'
    sync_item_class = TraktSyncNextEpisodeItem


class TraktSyncAllNextEpisodesMeta(SyncAllNextEpisodesMeta):
    meta_item_getter = TraktSyncAllNextEpisodesMetaItem
    sd_additional_keys = ('trakt_slug', )


class TraktSyncNextEpisodesMetaItem(SyncNextEpisodesMetaItem):
    sync_item_class = TraktSyncNextEpisodeItem


class TraktSyncNextEpisodesMeta(SyncNextEpisodesMeta):
    meta_item_getter = TraktSyncNextEpisodesMetaItem
    sd_additional_keys = ('trakt_slug', )
