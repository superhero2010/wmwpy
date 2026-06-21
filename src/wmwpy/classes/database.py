import sqlite3

from ..gameobject import GameObject
from ..utils.filesystem import *


class Database(GameObject):

    def __init__(
        self,
        database: str | bytes | File,
        filesystem: Filesystem | Folder = None,
        gamepath: str = None,
        assets: str = '/assets',
        baseassets: str = '/',
    ) -> None:
        """Game database object, which contains an sqlite3 database.

        Args:
            database (str | bytes | File): The database file.
            filesystem (Filesystem | Folder, optional): Filesystem to use. Defaults to None.
            gamepath (str, optional): Game path. Only used if filesystem not specified. Defaults to None.
            assets (str, optional): Assets path relative to game path. Only used if filesystem not specified. Defaults to '/assets'.
            baseassets (str, optional): Base assets path within the assets folder, e.g. `/perry/` in wmp. Defaults to `/`
        """
        super().__init__(filesystem, gamepath, assets, baseassets)

        self.connection = None

        self.filename = 'water.db'

        if isinstance(database, File):
            self.connection = database.read(mime = 'application/x-sqlite3')
            self.filename = database.path
        elif isinstance(database, str):
            file = File(None, 'water.db', bytes(database))
            self.connection = file.read()
        elif isinstance(database, bytes):
            file = File(None, 'water.db', database)
            self.connection = file.read()
        else:
            self.connection(':memory:')

    @property
    def connection(self) -> sqlite3.Connection:
        """The sqlite3 python database object.

        Returns:
            sqlite3.Connection: sqlite3 database connection
        """
        return self._connection

    @connection.setter
    def connection(self, connection: sqlite3.Connection):
        if connection == None:
            self._connection = None
            self.cursor = None
            return

        if not isinstance(connection, sqlite3.Connection):
            raise TypeError('connection must be sqlite3.Connection')

        self._connection = connection
        self.cursor = self._connection.cursor()

    def export(self, filename: str = None) -> bytes:
        """Export the database into the filesystem.

        Args:
            filename (str, optional): The filename of the database. Defaults to None.

        Returns:
            bytes: Output file in bytes.
        """
        if filename == None:
            filename = self.filename
        else:
            self.filename = filename

        file = self.filesystem.get(filename)

        if file == None:
            file = File(None, 'water.db', b'')

        data = file.write(self.connection)

        return file.rawdata.getvalue()

    def execute(self, *args):
        """Execute sql on the database. See sqlite3.Cursor.execute for parameters.

        Args:
            The arguments for sqlite3.Cursor.execute()

        Returns:
            sqlite3.Cursor: The sqlite3 Cursor object.
        """
        return self.cursor.execute(*args)
