from sqlite3 import connect
from hashlib import sha512
from getpass import getpass
import sys

DB_NAME = 'GameNet.db'
SALT = 'GameNetSalt'

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
    salted = (SALT + password).encode('utf-8')
    password = sha512(salted).hexdigest()
    cursor = connection.cursor()

    query = '''
        INSERT INTO `users` (`name`, `password`)
        VALUES ('{name}', '{password}');
        '''.format(name=username, password=password)
    cursor.execute(query)

    connection.commit()

if __name__ == '__main__':

    if len(sys.argv) < 2:
        quit()

    with connect(DB_NAME) as connection:
    
        if sys.argv[1] == 'create_tables':
            create_tables(connection)

        elif sys.argv[1] == 'add_user':
            username = input('Username: ')
            password = getpass()
            add_user(connection, username, password)
