from datetime import timezone
from jurialmunkey.ftools import cached_property
from tmdbhelper.lib.addon.tmdate import (
    convert_timestamp,
    datetime_in_range,
    get_datetime_utcnow,
    is_unaired_timestamp,
)


class TraktEpisodeAiring:
    """Compare Trakt's UTC broadcast timestamps without discarding the time."""

    def __init__(self, first_aired):
        self.first_aired = first_aired

    @property
    def has_airtime(self):
        return bool(self.first_aired and len(self.first_aired) > 10)

    @cached_property
    def datetime(self):
        return self.get_datetime()

    def get_datetime(self):
        if not self.has_airtime:
            return convert_timestamp(self.first_aired, time_fmt='%Y-%m-%d', time_lim=10)
        return convert_timestamp(self.first_aired).replace(tzinfo=timezone.utc)

    @cached_property
    def is_unaired(self):
        return self.get_is_unaired()

    def get_is_unaired(self):
        if not self.has_airtime:
            return is_unaired_timestamp(self.first_aired)
        return self.datetime > get_datetime_utcnow()

    def is_in_range(self, startdate, days):
        date = self.datetime.astimezone() if self.has_airtime else self.datetime
        return datetime_in_range(date, start_date=startdate, days=days)
