from jurialmunkey.ftools import cached_property
from tmdbhelper.lib.addon.plugin import get_localized
from tmdbhelper.lib.script.method.kodi_utils import container_refresh
from tmdbhelper.lib.sync.providers.list_actions import ListActions
from xbmcgui import Dialog


class TraktListActions(ListActions):
    def like_list(self, list_slug, user_slug='me', delete=False):
        item_class = ItemLikeOfficialList if user_slug == 'official' else ItemLikeList
        item = item_class(
            self.provider,
            user_slug=user_slug,
            list_slug=list_slug,
            confirmation=True,
            delete=delete)
        item.sync()
        if delete:
            container_refresh()

    def rename_list(self, list_slug):
        name = Dialog().input(get_localized(32359))
        if not name:
            return
        self.provider.api.post_response(
            'users/me/lists', list_slug,
            postdata={'name': name}, response_method='put')
        container_refresh()

    def delete_list(self, list_slug):
        if not Dialog().yesno(get_localized(32358), get_localized(32357).format(list_slug)):
            return
        self.provider.api.delete_response('users/me/lists', list_slug)
        container_refresh()


class ItemLikeList:
    def __init__(
            self, provider, user_slug, list_slug,
            confirmation=False, delete=False):
        self.provider = provider
        self.user_slug = user_slug
        self.list_slug = list_slug
        self.confirmation = confirmation
        self.delete = delete

    @cached_property
    def trakt_api(self):
        return self.get_trakt_api()

    def get_trakt_api(self):
        return self.provider.api

    @cached_property
    def request_args(self):
        return self.get_request_args()

    def get_request_args(self):
        return ('users', self.user_slug, 'lists', self.list_slug, 'like')

    @cached_property
    def response(self):
        return self.get_response()

    def get_response(self):
        request = self.trakt_api.delete_response if self.delete else self.trakt_api.post_response
        return request(*self.request_args)

    @cached_property
    def is_successful(self):
        return self.get_is_successful()

    def get_is_successful(self):
        return self.response is not None and self.response.status_code == 204

    @cached_property
    def dialog_message(self):
        return self.get_dialog_message()

    def get_dialog_message(self):
        affix = get_localized(32320 if self.delete else 32321)
        body = [
            get_localized(32316 if self.is_successful else 32317).format(affix),
            get_localized(32168).format(self.list_slug, self.user_slug),
        ]
        if not self.is_successful and self.response is not None:
            body.append(get_localized(32318).format(self.response.status_code))
        return '\n'.join(body)

    def sync(self):
        successful = self.is_successful
        if self.confirmation:
            Dialog().ok(get_localized(32315), self.dialog_message)
        if successful:
            return self.response


class ItemLikeOfficialList(ItemLikeList):
    def get_request_args(self):
        return ('lists', self.list_slug, 'like')
