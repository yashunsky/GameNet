#!/usr/bin/env python3
#-*- coding: utf-8 -*-

def get_descendants(cursor, tag_id, recursive=False):
    '''Return tag's children (recursive=False)
    or all descendants' tree (recursive=True)
    `tag_id` id is also included in the result
    '''
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
    '''Return tag's parent (recursive=False)
    or all ancestries' branch (recursive=True) '''
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
    '''Return tags, having no parent'''
    query = '''
        SELECT id, name, parent_id FROM tags
        WHERE tags.parent_id IS NULL;
    '''

    cursor.execute(query)

    return cursor.fetchall()


def get_tag_branch(connection, tag_id, user_id, recursive=False):
    '''Return a tuple of tag's ancestries, the tag itself, and it's descendants '''
    # TODO: if user_id is not None, the user shoud see only tags
    # according to his access
    cursor = connection.cursor()

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
