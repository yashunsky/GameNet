from hashlib import sha512

SALT = 'GameNetSalt'

def salt_password(password):
    salted = (SALT + password).encode('utf-8')
    return sha512(salted).hexdigest()

def create_tables(connection):
    cursor = connection.cursor()
    query = '''
        CREATE TABLE `users` (
            `id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            `name` TEXT UNIQUE NOT NULL,
            `password` TEXT NOT NULL
            );
        '''
    cursor.execute(query)

    query = '''
        CREATE TABLE `groups` (
            `id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            `name` TEXT NOT NULL
            );
        '''
    cursor.execute(query)

    query = '''
        CREATE TABLE `membership` (
            `id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            `user_id` INTEGER NOT NULL,
            `group_id` INTEGER NOT NULL,
            UNIQUE (`user_id`, `group_id`)
            );
        '''
    cursor.execute(query)

    query = '''
        CREATE TABLE `tags` (
            `id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            `name` TEXT,
            `parent_id`
            );
        '''
    cursor.execute(query)

    query = '''
        CREATE TABLE `documents` (
            `id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            `sender_id` INTEGER,
            `user_recipient_id` INTEGER,
            `group_recipient_id` INTEGER,
            `access_password` TEXT,
            `header` TEXT,
            `data` TEXT
            );
        '''
    cursor.execute(query)

    query = '''
        CREATE TABLE `doc_tags` (
            `id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            `document_id` INTEGER NOT NULL,
            `tag_id` INTEGER NOT NULL
            );
        '''
    cursor.execute(query)

    query = '''
        CREATE TABLE `access_log` (
            `id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            `document_id` INTEGER NOT NULL,
            `user_id` INTEGER NOT NULL,
            `action` TEXT,
            `timestamp` TEXT
            );
        '''
    cursor.execute(query)

    query = '''
        CREATE TABLE `user_access` (
            `id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            `user_id` INTEGER NOT NULL,
            `tag_id` INTEGER NOT NULL,
            `read` TEXT,
            `write` TEXT,
            `view_log` TEXT,
            `delete_log` TEXT,
            `modify_log` TEXT,
            `view_header` TEXT,
            UNIQUE (`user_id`, `tag_id`)
            );
        '''
    cursor.execute(query)

    query = '''
        CREATE TABLE `group_access` (
            `id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            `group_id` INTEGER NOT NULL,
            `tag_id` INTEGER NOT NULL,
            `read` TEXT,
            `write` TEXT,
            `view_log` TEXT,
            `delete_log` TEXT,
            `modify_log` TEXT,
            `view_header` TEXT,
            UNIQUE (`group_id`, `group_id`)
            );
        '''
    cursor.execute(query)

    connection.commit()

def add_user(connection, username, password):
    password = salt_password(password)
    cursor = connection.cursor()

    query = '''
        INSERT INTO `users` (`name`, `password`)
        VALUES (?, ?);
        '''
    cursor.execute(query, (username, password))

    connection.commit()

    return cursor.lastrowid

def add_group(connection, name):
    cursor = connection.cursor()

    query = '''
        INSERT INTO `groups` (`name`)
        VALUES (?);
        '''
    cursor.execute(query, name)

    connection.commit()

    return cursor.lastrowid

def add_membership(connection, user_id, group_id):
    cursor = connection.cursor()

    query = '''
        INSERT INTO `membership` (`user_id`, `group_id`)
        VALUES (?, ?);
        '''
    cursor.execute(query, (user_id, group_id))

    connection.commit()

    return cursor.lastrowid

def add_tag(connection, name, parent_id):
    cursor = connection.cursor()

    query = '''
        INSERT INTO `tags` (`name`, `parent_id`)
        VALUES (?, ?);
        '''
    cursor.execute(query, (name, parent_id))

    connection.commit()

    return cursor.lastrowid

def add_tag_access(connection, fields):
    cursor = connection.cursor()

    if 'user_id' in fields:
        target = 'user'
    elif 'group_id' in fields:
        target = 'group'
    else:
        return None

    query = '''
        INSERT INTO `{target}_access` (`{target}_id`, `tag_id`, 
            `read`, `write`, `view_log`, `delete_log`, 
            `modify_log`,`view_header`
            ) VALUES (:{target}_id, :tag_id, :read, :write, :view_log,
            :delete_log, :modify_log, :view_log);
        '''.format(target=target)
    cursor.execute(query, fields)

    connection.commit()

    return cursor.lastrowid


def add_document(connection, sender_id, user_recipient_id,
                 group_recipient_id, access_password,
                 header, data):
    cursor = connection.cursor()

    password = salt_password(access_password)

    query = '''
        INSERT INTO `documents` (`sender_id`, `user_recipient_id`,
                                 `group_recipient_id`,
                                 `access_password`, `header`, `data`)
        VALUES (?, ?, ?, ?, ?, ?);
        '''
    cursor.execute(query, (sender_id, user_recipient_id,
                           group_recipient_id, password,
                           header, data))

    connection.commit()

    return cursor.lastrowid

def add_doc_tag(connection, document_id, tag_id):
    cursor = connection.cursor()

    query = '''
        INSERT INTO `doc_tags` (`document_id`, `tag_id`)
        VALUES (?, ?);
        '''
    cursor.execute(query, (document_id, tag_id))

    connection.commit()

    return cursor.lastrowid

def auth(connection, username, password):
    cursor = connection.cursor()
    password = salt_password(password)

    query = '''
        SELECT id FROM `users`
        WHERE `name` = ?
        AND `password` = ?;
    '''
    cursor.execute(query, (username, password))

    answer = cursor.fetchone()
    
    return str(answer[0]) if answer is not None else ''

def get_descendants(cursor, tag_id, recursive=False):

    if recursive:
        query = '''
            WITH RECURSIVE
                is_child(n) AS (
                    VALUES(:tag_id)
                    UNION
                    SELECT id FROM tags, is_child
                    WHERE tags.parent_id=is_child.n
                )
            SELECT id, name, parent_id FROM tags
            WHERE tags.id IN is_child;
        '''
    else:
        query = '''
            SELECT id, name, parent_id FROM tags
            WHERE tags.parent_id=:tag_id
            OR tags.id=:tag_id;
        '''

    cursor.execute(query, {'tag_id': tag_id})

    return cursor.fetchall()

def get_ancestries(cursor, init_parent_id, recursive=False):

    if recursive:
        query = '''
            WITH RECURSIVE
                is_parent(n) AS (
                    VALUES(:init_parent_id)
                    UNION
                    SELECT parent_id FROM tags, is_parent
                    WHERE tags.id=is_parent.n
                )
            SELECT id, name, parent_id FROM tags
            WHERE tags.id IN is_parent;
        '''
    else:
        query = '''
            SELECT id, name, parent_id FROM tags
            WHERE tags.id=:init_parent_id;
        '''

    cursor.execute(query, {'init_parent_id': init_parent_id})

    return cursor.fetchall()

def get_root(cursor, recursive=False):
    query = '''
        SELECT id, name, parent_id FROM tags
        WHERE tags.parent_id IS NULL;
    '''

    cursor.execute(query)

    return cursor.fetchall()


def get_tag_branch(connection, tag_id, user_id, recursive=False):

    cursor = connection.cursor()

    user_id = int(user_id)

    if tag_id:
        tag_id = int(tag_id)
        children_tree = get_descendants(cursor, tag_id, recursive)

        self_tag = [child for child in children_tree if child[0] == tag_id][0]

        children_tree.remove(self_tag)
        parent_branch = get_ancestries(cursor, self_tag[2], recursive)

    else: # 0, '', None
        children_tree = get_root(cursor, recursive)
        self_tag = None
        parent_branch = []

    return parent_branch, self_tag, children_tree

def get_tag_access(connection, tag_id, user_id=None, group_id=None):
    cursor = connection.cursor()
    
    keys = ['user_id', 'read', 'write', 'view_log',
            'delete_log', 'modify_log', 'view_header']
    key_string = ', '.join(['access.%s' % key for key in keys])
    
    if user_id is not None:
        target = 'user'
        additional_condition = 'WHERE `user_id` =:user_id'
    elif group_id is not None:
        target = 'group'
        additional_condition = 'WHERE `group_id` =:group_id'
    else:
        target = 'user'
        additional_condition = ''

    query = '''
        SELECT users.name, {key_string} FROM {target}_access AS access
        INNER JOIN users ON users.id=access.user_id
        WHERE `tag_id`=:tag_id {additional_condition};
    '''.format(key_string=key_string,
               target=target,
               additional_condition=additional_condition)

    if user_id is not None:
        cursor.execute(query, {'tag_id': tag_id, 'user_id': user_id})
    elif group_id is not None:
        cursor.execute(query, {'tag_id': tag_id, 'group_id': group_id})
    else:
        cursor.execute(query, {'tag_id': tag_id})

    keys.insert(0, 'name')

    answer = cursor.fetchall()

    return keys, answer

def check_access(connection, tag_id, user_id=None, group_id=None):
    cursor = connection.cursor()


    keys = ['read', 'write', 'view_log',
            'delete_log', 'modify_log', 'view_header']

    key_string = ', '.join(['`%s`' % key for key in keys])

    final_select = ',\n'.join(['''(SELECT `{key}` FROM `access`
                                  CROSS JOIN (
                                    SELECT MAX(level) as `max_level`
                                    FROM `access`)
                                  WHERE `{key}`<>0 OR `level`=`max_level`
                                  ORDER BY `level` LIMIT 1)'''.format(key=key) 
                               for key in keys])

    query = '''
        DROP VIEW IF EXISTS `access`;
        '''
    cursor.execute(query)

    query = '''   
        CREATE TEMP VIEW `access` AS
            WITH RECURSIVE
                is_parent(level, tag_id) AS (
                    VALUES(0, {tag_id})
                    UNION
                    SELECT is_parent.level+1, parent_id FROM tags, is_parent
                    WHERE tags.id=is_parent.tag_id AND parent_id is NOT NULL
                )
            SELECT level, {key_string} FROM is_parent 
            INNER JOIN user_access ON (user_access.tag_id = is_parent.tag_id 
                                       AND user_access.user_id={user_id});
            '''.format(key_string=key_string,
                       tag_id=int(tag_id),
                       user_id=int(user_id))

    cursor.execute(query)

    query = '''  
        SELECT {key_string} FROM (
            {final_select}
        );
    '''.format(key_string=key_string, final_select=final_select)
    cursor.execute(query)

    answer = cursor.fetchone()

    answer = [access=='1' for access in answer]

    return keys, answer

