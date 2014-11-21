#!/usr/bin/env python3
#-*- coding: utf-8 -*-

from hashlib import sha512

SALT = 'GameNetSalt'
GRANTED = '1'
DENIED = '-1'
DEFAULT = '0'

def salt_password(password):
    salted = (SALT + password).encode('utf-8')
    return sha512(salted).hexdigest()

def resolve_access(access_table):
    '''Resolve access_table: for each column,
    the access is granted if there is at least one GRANTED entry
    and no DENIED entries.
    '''
    answer = []

    for column in zip(*access_table): # Matrix transpose
        if DENIED in column:
            answer.append(DENIED)
        elif GRANTED in column:
            answer.append(GRANTED)
        else:
            answer.append(DEFAULT)

    return answer

def auth(connection, username, password):
    '''Auth function. Returns user's id on success, None on failure '''
    cursor = connection.cursor()
    password = salt_password(password)

    query = '''
        SELECT id FROM `users`
        WHERE `name` = ?
        AND `password` = ?;
    '''
    cursor.execute(query, (username, password))

    answer = cursor.fetchone()
    
    return answer[0] if answer is not None else None

def get_tag_access(connection, tag_id, user_id=None, group_id=None):
    '''Returns access for the user or for the group
       if no user_id niser group_id is specified, lists all
       available user's access entries.
    '''
    # TODO a non-specified request should return users and groups,
    # but I need to think about the implementation

    cursor = connection.cursor()

    params = {'tag_id': tag_id}
    additional_condition = 'WHERE `{target}_id` =:target_id'

    if user_id is not None:
        target = 'user'
        params['target_id'] = user_id
    elif group_id is not None:
        target = 'group'
        params['target_id'] = group_id
    else:
        target = 'user'
        additional_condition = ''
    
    keys = ['{}_id'.format(target), 'read', 'write', 'view_log',
            'delete_log', 'modify_log', 'view_header']
    key_string = ', '.join(['access.%s' % key for key in keys])
    
    query = '''
        SELECT users.name, {key_string} FROM {target}_access AS access
        INNER JOIN users ON users.id=access.user_id
        WHERE `tag_id`=:tag_id {additional_condition};
    '''.format(key_string=key_string,
               target=target,
               additional_condition=additional_condition)

    cursor.execute(query, params)

    keys.insert(0, 'name')

    answer = cursor.fetchall()

    return keys, answer

def access_process(access, to_bool, granted=GRANTED):
    '''(GRANTED, DEFAULT, DENIED) to (True, False) processing on demande'''
    if to_bool:
        return [value==granted for value in access]
    else:
        return access

def check_access(connection, tag_id, user_id=None, group_id=None, to_bool=True):
    '''Check if a specified user or group has access to the tag'''

    cursor = connection.cursor()

    keys = ['read', 'write', 'view_log',
            'delete_log', 'modify_log', 'view_header']

    if user_id is not None:
        target = 'user'
        target_id = user_id
    elif group_id is not None:
        target = 'group'
        target_id = group_id
    else:
        return keys, [False]*len(keys)

    key_string = ', '.join(['`%s`' % key for key in keys])

    query = '''   
        WITH RECURSIVE
            is_parent(level, tag_id) AS (
                VALUES(0, :tag_id)
                UNION
                SELECT is_parent.level+1, parent_id FROM tags, is_parent
                WHERE tags.id=is_parent.tag_id AND parent_id is NOT NULL
            )
        SELECT {key_string} FROM is_parent 
        INNER JOIN {target}_access ON ({target}_access.tag_id = is_parent.tag_id 
                                   AND {target}_access.{target}_id=:target_id)
        ORDER BY `level`;
        '''.format(key_string=key_string, target=target)

    cursor.execute(query, {'tag_id': tag_id, 'target_id': target_id})

    query_result = cursor.fetchall()

    answer = [DEFAULT]*len(keys)

    # Access is Granted or Denied according to the first non-Default
    # value, met in the recieved table
    for row in query_result:
        for position, value in enumerate(row):
            if answer[position] == DEFAULT:
                answer[position] = value

    return keys, access_process(answer, to_bool)

def get_user_groups(connection, user_id):
    cursor = connection.cursor()
    query = '''SELECT `group_id` FROM `membership` WHERE `user_id`=:user_id;'''
    cursor.execute(query, {'user_id': user_id})
    return cursor.fetchall()

def get_document_tags(connection, document_id):
    cursor = connection.cursor()
    query = '''SELECT `tag_id` FROM `doc_tags` WHERE `document_id`=:document_id;'''
    cursor.execute(query, {'document_id': document_id})
    return cursor.fetchall()

def check_tag_access(connection, tag_id, user_id, to_bool=True):
    '''Check if the user has acccess to the tag
    data about user's and all it's groups access is unioned and resolved
    as written in resolve_access function
    '''
    user_groups = get_user_groups(connection, user_id)

    keys, user_access = check_access(connection, tag_id,
                                     user_id=user_id, to_bool=False)
    
    access_table = [user_access]
    for group_id in user_groups:
        keys, group_access = check_access(connection, tag_id,
                                          group_id=group_id[0],
                                          to_bool=False)
        access_table.append(group_access)

    answer = resolve_access(access_table)
    
    return keys, access_process(answer, to_bool)

def check_doc_access(connection, document_id, user_id, to_bool=True):
    '''Check if the user has access to the documents, according to his
    access to each document's tag'''
    document_tags = get_document_tags(connection, document_id)

    access_table = []
    for tag_id in document_tags:
        keys, answer = check_tag_access(connection, tag_id, user_id, to_bool=False)
        access_table.extend(answer)

    answer = resolve_access(access_table)
    
    return keys, access_process(answer, to_bool)