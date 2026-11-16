from jurialmunkey.ftools import cached_property
from contextlib import closing
from tmdbhelper.lib.addon.consts import DEFAULT_EXPIRY
from tmdbhelper.lib.addon.tmdate import set_timestamp
from tmdbhelper.lib.files.dbdata import Database, DatabaseStatements
from tmdbhelper.lib.files.dbfunc import DatabaseAccess
from tmdbhelper_sync_trakt.identifiers.tabledef import IDENTIFIER_COLUMNS


class TraktIdentifiersDatabase(Database):
    database_tables = {
        'identifiers': IDENTIFIER_COLUMNS,
        'queries': {'id': {'data': 'TEXT PRIMARY KEY'}, 'expiry': {'data': 'INTEGER'}},
    }

    def __init__(self):
        super().__init__(filename='TraktIdentifiers.db')

    @cached_property
    def access(self):
        return self.get_access()

    def get_access(self):
        access = DatabaseAccess()
        access.cache = self
        return access

    @property
    def current_time(self):
        return set_timestamp(0, set_int=True)

    def is_queried(self, query):
        with self.session():
            expiry = self.access.get_cached('queries', query, 'expiry') or 0
        return expiry > self.current_time

    def get_item(self, id_value, id_type, item_type, season=None, episode=None):
        # A bare episode TMDb ID identifies the episode, never its parent show.
        column = 'tmdb_ep' if id_type == 'tmdb' and item_type == 'episode' and season is None else f'{id_type}_id'
        if column not in IDENTIFIER_COLUMNS:
            raise ValueError(f'Unsupported identifier type: {id_type}')
        conditions = [f'{column}=?', 'item_type=?', 'expiry>?']
        values = [id_value, item_type, self.current_time]
        for name, value in (('season', season), ('episode', episode)):
            if value is not None:
                conditions.append(f'{name}=?')
                values.append(int(value))
        with self.session():
            rows = self.access.get_cached_list_values(
                'identifiers', tuple(IDENTIFIER_COLUMNS), tuple(values), ' AND '.join(conditions))
        return dict(rows[0]) if rows else None

    def save_items(self, query, items):
        expiry = self.current_time + DEFAULT_EXPIRY
        keys = tuple(IDENTIFIER_COLUMNS)
        values = [tuple(dict(item, expiry=expiry)[key] for key in keys) for item in items]
        with closing(self.get_database()) as connection, connection:
            connection.executemany(DatabaseStatements.insert_or_replace('identifiers', keys), values)
            connection.execute(DatabaseStatements.insert_or_replace('queries', ('id', 'expiry')), (query, expiry))

    def migrate_legacy_cache(self):
        marker = 'legacy-cache-imported'
        with closing(self.get_database()) as connection, connection:
            if connection.execute('SELECT id FROM queries WHERE id=?', (marker,)).fetchone() is not None:
                return
            rows = self.get_legacy_items()
            keys = tuple(IDENTIFIER_COLUMNS)
            values = [tuple(row[key] for key in keys) for row in rows]
            connection.executemany(DatabaseStatements.insert_or_ignore('identifiers', keys), values)
            connection.execute(
                DatabaseStatements.insert_or_replace('queries', ('id', 'expiry')),
                (marker, self.current_time))

    def get_legacy_items(self):
        from tmdbhelper.lib.query.database.database import FindQueriesDatabase
        legacy = FindQueriesDatabase()
        connection = legacy.get_database(read_only=True)
        try:
            table = connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trakt_id'").fetchone()
            if table is None:
                return []
            expiry = connection.execute("SELECT expiry FROM expiry WHERE id='trakt_id'").fetchone()
            if expiry is None or expiry['expiry'] <= self.current_time:
                return []
            return [
                dict(row, episode_slug_id=None, expiry=expiry['expiry'])
                for row in connection.execute('SELECT * FROM trakt_id').fetchall()]
        finally:
            connection.close()
