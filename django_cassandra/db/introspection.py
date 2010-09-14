from djangotoolbox.db.base import NonrelDatabaseIntrospection
from django.db.backends import BaseDatabaseIntrospection
#from cassandra import Cassandra
#from cassandra.ttypes import *

class DatabaseIntrospection(NonrelDatabaseIntrospection):
    def get_table_list(self, cursor):
        "Returns a list of names of all tables that exist in the database."
        client = self.connection.db_connection.client
        settings_dict = self.connection.settings_dict
        keyspace_name = settings_dict['NAME']
        ks_def = client.describe_keyspace(keyspace_name)
        result = [cf_def.name for cf_def in ks_def.cf_defs]
        return result
    
    def table_names(self):
        # NonrelDatabaseIntrospection has an implementation of this that returns
        # that all of the tables for the models already exist in the database,
        # so the DatabaseCreation code never gets called to create new tables,
        # which isn't how we want things to work for Cassandra, so we bypass the
        # nonrel implementation and go directly to the base introspection code.
        return BaseDatabaseIntrospection.table_names(self)

    def sequence_list(self):
        return []
    
# Implement these things eventually
#===============================================================================
#    def get_table_description(self, cursor, table_name):
#        "Returns a description of the table, with the DB-API cursor.description interface."
#        return ""
# 
#    def get_relations(self, cursor, table_name):
#        """
#        Returns a dictionary of {field_index: (field_index_other_table, other_table)}
#        representing all relationships to the given table. Indexes are 0-based.
#        """
#        relations = {}
#        return relations
#    
#    def get_indexes(self, cursor, table_name):
#        """
#        Returns a dictionary of fieldname -> infodict for the given table,
#        where each infodict is in the format:
#            {'primary_key': boolean representing whether it's the primary key,
#             'unique': boolean representing whether it's a unique index}
#        """
#        indexes = {}
#        return indexes
#===============================================================================