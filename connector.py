import yaml
import pymysql
import warnings


try:
    config_file = open('config.yml')
except FileNotFoundError:
    config_file = open('example_config.yml')
finally:
    config = yaml.load(config_file, Loader=yaml.FullLoader)
    user, password, database = config['mysql']['user'], config['mysql']['pass'], config['mysql']['database']

db = pymysql.connect('localhost', user, password, database)

# def make_db():
#     """
#     DANGER: RESETS ALL DATA IN DATABASE
#     """
#     cursor = db.cursor()
#     cursor.execute("DROP TABLE IF EXISTS servers")
#     cursor.execute("""CREATE TABLE servers (
#         server_id BIGINT NOT NULL,
#         nickname_sync BOOLEAN,
#         role_sync BOOLEAN,
#         sync_source VARCHAR(20),
#         join_message BOOLEAN DEFAULT FALSE,
#         prefix VARCHAR(255),
#         PRIMARY KEY (server_id))""")
#     cursor.execute("DROP TABLE IF EXISTS subscriptions_contests")
#     cursor.execute("""CREATE TABLE subscriptions_contests (
#         channel_id BIGINT NOT NULL,
#         subint INT DEFAULT 63,
#         PRIMARY KEY (channel_id))""")
#     cursor.execute("DROP TABLE IF EXISTS users")
#     cursor.execute("""CREATE TABLE users (
#         user_id BIGINT NOT NULL,
#         tea INT,
#         dmoj VARCHAR(255),
#         last_dmoj_problem VARCHAR(255),
#         can_repeat BOOLEAN,
#         codeforces VARCHAR(255),
#         country VARCHAR(255),
#         can_suggest BOOLEAN,
#         PRIMARY KEY (user_id))""")
#     cursor.execute("SHOW TABLES")
#     result = cursor.fetchall()
#     print("Tables:")
#     for data in result:
#         print(data[0])

class MySQLConnection(object):
    def sanitize_id(self, id):
        try:
            return str(id).isdigit()
        except TypeError:
            return False
        return True

    def sanitize_alnum(self, *args):
        try:
            for value in args:
                if not str(value).replace('_', '').isalnum():
                    return False
        except TypeError:
            return False
        return True

    def set_query(self, sql):
        cursor = db.cursor()
        try:
            cursor.execute(sql)
            db.commit()
        except pymysql.Error as e:
            db.rollback()
            raise e

    def readall_query(self, sql):
        cursor = db.cursor()
        cursor.execute(sql)
        return cursor.fetchall()
    
    def readone_query(self, sql):
        cursor = db.cursor()
        cursor.execute(sql)
        return cursor.fetchone()

    def table_size(self, table):
        if not self.sanitize_alnum(table):
            return -1
        return self.readone_query("SELECT COUNT(*) FROM %s" % table)[0]

    def exists(self, table, id_name, id):
        if not self.sanitize_alnum(table, id_name, id):
            return -1
        sql = "SELECT EXISTS(SELECT * FROM %s WHERE %s = %d)" % (table, id_name, id)
        return self.readone_query(sql)[0]

    def insert_ignore_user(self, user_id):
        if not self.sanitize_id(user_id):
            return -1
        sql = "INSERT IGNORE INTO users(user_id, tea, dmoj, last_dmoj_problem, can_repeat, codeforces, country, can_suggest) \
            VALUES (%d, 0, NULL, NULL, TRUE, NULL, NULL, TRUE)" % \
            (user_id)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.set_query(sql)
        return 0

    def user_count(self):
        sql = "SELECT COUNT(*) FROM users"
        return self.readone_query(sql)[0]

    def get_global_countries(self):
        sql = "SELECT DISTINCT country FROM users WHERE country IS NOT NULL"
        result = self.readall_query(sql)
        countries = []
        for row in result:
            sql = "SELECT COUNT(*) FROM users WHERE country='%s'" % row[0]
            countries.append(row[0] + ' - ' + str(self.readone_query(sql)[0]))
        return countries

    def get_global_linked_count(self, row):
        if not self.sanitize_alnum(row):
            return -1
        sql = "SELECT COUNT(*) FROM users WHERE %s IS NOT NULL" % row
        return self.readone_query(sql)[0]

    def get_server(self, server_id):
        if not self.sanitize_id(server_id):
            return -1
        sql = "SELECT * FROM servers WHERE server_id = %d" % server_id
        row = self.readone_query(sql)
        if row is None:
            return {}
        server = {
            row[0]: {
                'nickname_sync': row[1],
                'role_sync': row[2],
                'sync_source': row[3],
                'join_message': row[4],
                'prefix': row[5]
            }
        }
        return server

    def get_user(self, user_id):
        if not self.sanitize_id(user_id):
            return -1
        sql = "SELECT * FROM users WHERE user_id = %d" % user_id
        row = self.readone_query(sql)
        if row is None:
            return {}
        user = {
            row[0]: {
                'tea': row[1],
                'dmoj': row[2],
                'last_dmoj_problem': row[3],
                'can_repeat': row[4],
                'codeforces': row[5],
                'country': row[6],
                'can_suggest': row[7]
            }
        }
        return user

    def get_user_by_row(self, row, key):
        if not self.sanitize_id(row):
            return -1
        if not self.sanitize_alnum(key):
            return -1
        sql = "SELECT user_id, %s FROM (SELECT * FROM users LIMIT %d, %d) AS u WHERE u.%s IS NOT NULL" % \
            (key, row, self.table_size('users')-row, key)
        result = self.readone_query(sql)
        if result is None:
            return 0, {}
        sql2 = "SELECT * FROM  (SELECT ROW_NUMBER() OVER ( ORDER BY user_id ) AS row_num, user_id FROM users) \
                AS eu WHERE user_id='%s'" % (result[0])
        new_row = self.readone_query(sql2)[0] + 1
        user_data = {
            'user_id': int(result[0]),
            key: result[1]
        }
        return new_row, user_data

    def get_next_user_by_row(self, row, key):
        if row >= self.table_size('users'):
            row = 0
        return self.get_user_by_row(row, key)

    def var_to_sql(self, value):
        if value is None:
            return "NULL"
        elif value is True:
            return "TRUE"
        elif value is False:
            return "False"
        elif type(value) is int:
            return value
        return "'%s'" % value

    def update_user(self, user_id, field, value):
        if not self.sanitize_alnum(field, value) or not self.sanitize_id(user_id):
            return -1
        sql = "UPDATE users SET %s = %s \
                WHERE user_id = %d" % \
                (field, self.var_to_sql(value), user_id)
        self.set_query(sql)
        return 0

    def insert_ignore_server(self, server_id):
        if not self.sanitize_id(server_id):
            return -1
        sql = "INSERT IGNORE INTO servers(server_id, nickname_sync, role_sync, sync_source, join_message) \
            VALUES (%d, FALSE, FALSE, 'dmoj', FALSE)" % \
            (server_id)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.set_query(sql)
        return 0

    def update_server(self, server_id, field, value):
        if not self.sanitize_alnum(field, value) or not self.sanitize_id(server_id):
            return -1
        sql = "UPDATE servers SET %s = %s \
                WHERE server_id = %d" % \
                (field, self.var_to_sql(value), server_id)
        self.set_query(sql)
        return 0

    def update_server_prefix(self, server_id, fix):
        sql = "UPDATE servers SET prefix = '%s' WHERE server_id = %d" % (fix, server_id)
        self.set_query(sql)
        return 0

    def get_prefixes(self):
        sql = "SELECT * FROM servers \
        WHERE prefix IS NOT NULL"
        result = self.readall_query(sql)
        server_to_prefix = {}
        for row in result:
            server_to_prefix[row[0]] = row[4]
        return server_to_prefix

    def get_prefix(self, server_id):
        if not self.sanitize_id(server_id):
            return None
        sql = "SELECT prefix FROM servers \
        WHERE server_id=%d" % server_id
        return self.readone_query(sql)[0]

    def get_all_sync_source(self):
        sql = "SELECT server_id, sync_source from servers"
        result = self.readall_query(sql)
        sync_sources = {}
        for row in result:
            sync_sources[row[0]] = row[1]
        return sync_sources

    def get_all_role_sync(self, site):
        if not self.sanitize_alnum(site):
            return -1
        sql = "SELECT * FROM servers \
        WHERE role_sync AND sync_source = '%s'" % site
        result = self.readall_query(sql)
        servers = []
        for row in result:
            servers.append(row[0])
        return servers

    def get_all_nick_sync(self, site):
        if not self.sanitize_alnum(site):
            return -1
        sql = "SELECT * FROM servers \
        WHERE nickname_sync AND sync_source = '%s'" % site
        result = self.readall_query(sql)
        servers = []
        for row in result:
            servers.append(row[0])
        return servers

    def get_join_message(self, server_id):
        if not self.sanitize_id(server_id):
            return -1
        sql = "SELECT join_message from servers WHERE server_id = %d" % server_id
        result = self.readone_query(sql)
        if result is None:
            return False
        return result[0]

    def get_cf_handles(self):
        sql = "SELECT user_id, codeforces FROM users WHERE codeforces IS NOT NULL"
        result = self.readall_query(sql)
        handles = {}
        for row in result:
            handles[row[1]] = row[0]
        return handles

    def get_subbed_ojs(self, channel_id):
        if not self.sanitize_id(channel_id):
            return -1
        sql = "SELECT subint FROM subscriptions_contests WHERE channel_id = %d" % channel_id
        result = self.readone_query(sql)
        if result is None:
            return False
        return result[0]

    def update_subbed_ojs(self, channel_id, subint):
        sql = "UPDATE subscriptions_contests SET subint = '%s' WHERE channel_id = %d" % (subint, channel_id)
        self.set_query(sql)
        return 0

    def sub_channel(self, channel_id):
        if not self.sanitize_id(channel_id):
            return -1
        sql = "INSERT INTO subscriptions_contests(channel_id) \
            VALUES (%d)" % \
            (channel_id)
        self.set_query(sql)
        return 0

    def unsub_channel(self, channel_id):
        if not self.sanitize_id(channel_id):
            return -1
        sql = "DELETE FROM subscriptions_contests WHERE channel_id = %d" % channel_id
        self.set_query(sql)
        return 0

    def get_all_subs(self):
        sql = "SELECT channel_id FROM subscriptions_contests"
        result = self.readall_query(sql)
        channels = []
        for row in result:
            channels.append(row[0])
        return channels

if __name__ == "__main__":
    cursor = db.cursor()
    cursor.execute("SELECT VERSION()")
    data = cursor.fetchone()
    print("Database version: %s " % data)
    db.close()

mySQLConnection = MySQLConnection()
