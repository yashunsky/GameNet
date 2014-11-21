#!/usr/bin/env python3
#-*- coding: utf-8 -*-

from hashlib import sha512

from .access import SALT
from .access import salt_password

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
    '''Add access entrie for a user or a group,
    depending on witch key is present in fields'''
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
            :delete_log, :modify_log, :view_header);
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

