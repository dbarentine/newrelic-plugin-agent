"""
MongoDB Support

"""
import datetime
from pymongo import errors
import logging
import pymongo

from newrelic_plugin_agent.plugins import base

LOGGER = logging.getLogger(__name__)


class MongoDB(base.Plugin):

    GUID = 'com.dell.software.newrelic_mongodb_plugin_agent'

    def add_datapoints(self, name, stats):
        """Add all of the data points for a database

        :param str name: The name of the database for the stats
        :param dict stats: The stats data to add

        """
        base_key = 'Database/%s' % name
        self.add_gauge_value('%s/Extents' % base_key, 'extents',
                             stats.get('numExtents', 0))
        self.add_gauge_value('%s/Size' % base_key, 'bytes',
                             stats.get('dataSize', 0))
        self.add_gauge_value('%s/Storage Size' % base_key, 'bytes',
                             stats.get('storageSize', 0))
        self.add_gauge_value('%s/Objects/Count' % base_key, 'objects',
                             stats.get('objects', 0))
        self.add_gauge_value('%s/Objects/Average Size' % base_key, 'bytes',
                             stats.get('avgObjSize', 0))
        self.add_gauge_value('%s/Collections' % base_key, 'collections',
                             stats.get('collections', 0))
        self.add_gauge_value('%s/Index/Count' % base_key, 'indexes',
                             stats.get('indexes', 0))
        self.add_gauge_value('%s/Index/Size' % base_key, 'bytes',
                             stats.get('indexSize', 0))

    def add_server_datapoints(self, stats):
        """Add all of the data points for a server

        :param dict stats: The stats data to add

        """
        asserts = stats.get('asserts', dict())
        self.add_derive_value('Asserts/Regular', 'asserts',
                              asserts.get('regular', 0))
        self.add_derive_value('Asserts/Warning', 'asserts',
                              asserts.get('warning', 0))
        self.add_derive_value('Asserts/Message', 'asserts',
                              asserts.get('msg', 0))
        self.add_derive_value('Asserts/User', 'asserts',
                              asserts.get('user', 0))
        self.add_derive_value('Asserts/Rollovers', 'asserts',
                              asserts.get('rollovers', 0))

        conn = stats.get('connections', dict())
        self.add_gauge_value('Connections/Available', 'connections',
                             conn.get('available', 0))
        self.add_gauge_value('Connections/Current', 'connections',
                             conn.get('current', 0))

        cursors = stats.get('cursors', dict())
        self.add_gauge_value('Cursors/Open', 'cursors',
                             cursors.get('totalOpen', 0))
        self.add_derive_value('Cursors/Timed Out', 'cursors',
                              cursors.get('timedOut', 0))

        locks = stats.get('globalLock', dict())
        self.add_derive_value('Global Locks/Held', 'ms',
                              locks.get('totalTime', 0) / 1000)

        active = locks.get('activeClients', dict())
        self.add_derive_value('Global Locks/Active Clients/Total', 'clients',
                              active.get('total', 0))
        self.add_derive_value('Global Locks/Active Clients/Readers', 'clients',
                              active.get('readers', 0))
        self.add_derive_value('Global Locks/Active Clients/Writers', 'clients',
                              active.get('writers', 0))

        queue = locks.get('currentQueue', dict())
        self.add_derive_value('Global Locks/Queue/Total', 'locks',
                              queue.get('total', 0))
        self.add_derive_value('Global Locks/Queue/Readers', 'readers',
                              queue.get('readers', 0))
        self.add_derive_value('Global Locks/Queue/Writers', 'writers',
                              queue.get('writers', 0))

        mem = stats.get('mem', dict())
        self.add_gauge_value('Memory/Mapped', 'bytes',
                             mem.get('mapped', 0) / 1048576)
        self.add_gauge_value('Memory/Mapped with Journal', 'bytes',
                             mem.get('mappedWithJournal', 0) / 1048576)
        self.add_gauge_value('Memory/Resident', 'bytes',
                             mem.get('resident', 0) / 1048576)
        self.add_gauge_value('Memory/Virtual', 'bytes',
                             mem.get('virtual', 0) / 1048576)

        net = stats.get('network', dict())
        self.add_derive_value('Network/Requests', 'requests',
                              net.get('numRequests', 0))
        self.add_derive_value('Network/Transfer/In', 'bytes',
                              net.get('bytesIn', 0))
        self.add_derive_value('Network/Transfer/Out', 'bytes',
                              net.get('bytesOut', 0))

        ops = stats.get('opcounters', dict())
        self.add_derive_value('Operations/Insert', 'ops', ops.get('insert', 0))
        self.add_derive_value('Operations/Query', 'ops', ops.get('query', 0))
        self.add_derive_value('Operations/Update', 'ops', ops.get('update', 0))
        self.add_derive_value('Operations/Delete', 'ops', ops.get('delete', 0))
        self.add_derive_value('Operations/Get More', 'ops',
                              ops.get('getmore', 0))
        self.add_derive_value('Operations/Command', 'ops',
                              ops.get('command', 0))

        ops = stats.get('opcountersRepl', dict())
        self.add_derive_value('Replication Operations/Insert', 'ops', ops.get('insert', 0))
        self.add_derive_value('Replication Operations/Query', 'ops', ops.get('query', 0))
        self.add_derive_value('Replication Operations/Update', 'ops', ops.get('update', 0))
        self.add_derive_value('Replication Replication Operations/Delete', 'ops', ops.get('delete', 0))
        self.add_derive_value('Operations/Get More', 'ops',
                              ops.get('getmore', 0))
        self.add_derive_value('Replication Operations/Command', 'ops',
                              ops.get('command', 0))

        extra = stats.get('extra_info', dict())
        self.add_gauge_value('System/Heap Usage', 'bytes',
                             extra.get('heap_usage_bytes', 0))
        self.add_derive_value('System/Page Faults', 'faults',
                              extra.get('page_faults', 0))

    def connect(self):
        kwargs = {'host': self.config.get('host', 'localhost'),
                  'port': self.config.get('port', 27017)}
        for key in ['ssl', 'ssl_keyfile', 'ssl_certfile',
                    'ssl_cert_reqs', 'ssl_ca_certs']:
            if key in self.config:
                kwargs[key] = self.config[key]
        try:
            return pymongo.MongoClient(**kwargs)
        except pymongo.errors.ConnectionFailure as error:
            LOGGER.error('Could not connect to MongoDB: %s', error)

    def get_and_add_db_stats(self):
        """Fetch the data from the MongoDB server and add the datapoints

        """
        databases = self.config.get('databases', list())
        if isinstance(databases, list):
            self.get_and_add_db_list(databases)
        else:
            self.get_and_add_db_dict(databases)

    def get_and_add_db_list(self, databases):
        """Handle the list of databases while supporting authentication for
        the admin if needed

        :param list databases: The database list

        """
        LOGGER.debug('Processing list of mongo databases')
        client = self.connect()
        if not client:
            return
        for database in databases:
            LOGGER.debug('Collecting stats for %s', database)
            db = client[database]
            try:
                self.add_datapoints(database, db.command('dbStats'))
            except errors.OperationFailure as error:
                LOGGER.critical('Could not fetch stats: %s', error)

		client.close()

    def get_and_add_db_dict(self, databases):
        """Handle the nested database structure with username and password.

        :param dict databases: The databases data structure

        """
        LOGGER.debug('Processing dict of mongo databases')
        client = self.connect()
        if not client:
            return
        db_names = databases.keys()
        for database in db_names:
            db = client[database]
            try:
                if 'username' in databases[database]:
                    db.authenticate(databases[database]['username'],
                                    databases[database].get('password'))
                self.add_datapoints(database, db.command('dbStats'))
                if 'username' in databases[database]:
                    db.logout()
            except errors.OperationFailure as error:
                LOGGER.critical('Could not fetch stats: %s', error)

		client.close()

    def get_and_add_server_stats(self):
        LOGGER.debug('Fetching server stats')
        client = self.connect()
        if not client:
            return
        if self.config.get('admin_username'):
            client.admin.authenticate(self.config['admin_username'],
                                   self.config.get('admin_password'))
        self.add_server_datapoints(client.db.command('serverStatus'))
        client.close()

    def poll(self):
        self.initialize()
        self.get_and_add_server_stats()
        self.get_and_add_db_stats()
        self.finish()
