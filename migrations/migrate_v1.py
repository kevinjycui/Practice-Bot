import json
from backend import mySQLConnection as query
from backend import make_db, db

if __name__ == "__main__":
    '''
    Migrating data from old JSON files to MySQL
    '''

    make_db()

    with open('data/server_nicks.json') as f:
        server_nicks = json.load(f)

    with open('data/server_roles.json') as f:
        server_roles = json.load(f)

    with open('data/subscriptions.json') as f:
        subscriptions = json.load(f)

    with open('data/users.json') as f:
        users = json.load(f)

    for server in server_nicks:
        query.set_query("INSERT INTO servers(server_id, nickname_sync, role_sync, sync_source) \
            VALUES (%d, TRUE, FALSE, 'dmoj')" % \
            (server))

    for server in server_roles:
        if query.exists('servers', 'server_id', server):
            query.update_server(server, 'role_sync', True)
        else:
            query.set_query("INSERT INTO servers(server_id, nickname_sync, role_sync, sync_source) \
                VALUES (%d, FALSE, TRUE, 'dmoj')" % \
                (server))

    for channel in subscriptions:
        query.sub_channel(int(channel))

    for user, data in list(users.items()):
        query.set_query("INSERT INTO users(user_id, tea, dmoj, last_dmoj_problem, can_repeat) \
                VALUES (%d, %d, %s, %s, %s)" % \
                (int(user), data.get('tea', 0), query.var_to_sql(data.get('dmoj', None)), query.var_to_sql(data.get('last_dmoj_problem', None)), query.var_to_sql(data.get('can_repeat', False))))

    cursor = db.cursor()
    cursor.execute("SELECT * FROM subscriptions_contests")
    data = cursor.fetchall()
    print('=====================')
    print('Subscription Contests')
    print('---------------------')
    for row in data:
        print(*row)
    print('=====================')
    print()

    print('=====================')
    print('Servers')
    print('---------------------')
    print('server_id | nickname_sync | role_sync | sync_source')
    print('---------------------')
    cursor.execute("SELECT * FROM servers")
    data = cursor.fetchall()
    for row in data:
        print(' | '.join(map(str, row)))
    print('=====================')
    print()

    print('=====================')
    print('Users')
    print('---------------------')
    print('user_id | tea | dmoj | last_dmoj_problem | can_repeat')
    print('---------------------')
    cursor.execute("SELECT * FROM users")
    data = cursor.fetchall()
    for row in data:
        print(' | '.join(map(str, row)))
    print('=====================')
    print()

    db.close()
