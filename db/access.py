from hashlib import sha512

SALT = 'GameNetSalt'
GRANTED = '1'
DENIED = '-1'
DEFAULT = '0'

def salt_password(password):
    salted = (SALT + password).encode('utf-8')
    return sha512(salted).hexdigest()

def resolve_access(access_table):
    answer = []

    for column in zip(*access_table): # Matrix transpose :)
        if DENIED in column:
            answer.append(DENIED)
        elif GRANTED in column:
            answer.append(GRANTED)
        else:
            answer.append(DEFAULT)

    return answer

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

def access_process(access, to_bool, granted=GRANTED):
    if to_bool:
        return [value==granted for value in access]
    else:
        return access

def check_access(connection, tag_id, user_id=None, group_id=None, to_bool=True):
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
    
    user_groups = get_user_groups(connection, user_id)

    keys, user_access = check_access(connection, tag_id,
                                     user_id=user_id, to_bool=False)
    
    access_table = [user_access]
    for group_id in user_groups:
        keys, group_access = check_access(connection, tag_id,
                                     group_id=group_id[0], to_bool=False)
        access_table.append(group_access)

    answer = resolve_access(access_table)
    
    return keys, access_process(answer, to_bool)

def check_doc_access(connection, document_id, user_id, to_bool=True):
    document_tags = get_document_tags(connection, document_id)

    access_table = []
    for tag_id in document_tags:
        keys, answer = check_tag_access(connection, tag_id, user_id, to_bool=False)
        access_table.extend(answer)

    answer = resolve_access(access_table)
    
    return keys, access_process(answer, to_bool)