from .item import ItemSync
from tmdbhelper.lib.script.sync.actions import (
    ItemWatched as BasicItemWatched,
    ItemUnwatched as BasicItemUnwatched,
    ItemWatchlist as BasicItemWatchlist,
    ItemCollection as BasicItemCollection,
    ItemDropped as BasicItemDropped,
)


class ItemWatched(ItemSync, BasicItemWatched):
    sync_url = 'history'


class ItemUnwatched(ItemSync, BasicItemUnwatched):
    sync_url = 'history'


class ItemWatchlist(ItemSync, BasicItemWatchlist):
    sync_url = 'watchlist'


class ItemCollection(ItemSync, BasicItemCollection):
    sync_url = 'collection'


class ItemFavorites(ItemSync):
    localized_name_add = 32490
    localized_name_rem = 32491
    sync_key = 'favorites_listed_at'
    sync_url = 'favorites'


class ItemDropped(ItemSync, BasicItemDropped):
    sync_url = 'hidden/dropped'

    def get_post_response_args(self):
        return ('users', self.method, )
