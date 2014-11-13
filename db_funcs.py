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
            `name` TEXT NOT NULL,
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
            `group_id` INTEGER NOT NULL
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
            `action` TEXT
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
            `view_header` TEXT
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
            `view_header` TEXT
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

def get_tag_branch(connection, tag_id, user_id):

    return ':DK'


