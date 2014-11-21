from sqlite3 import connect
from getpass import getpass
import sys

from db.init_db import create_tables
from db.add_entries import add_user, add_tag, add_document, add_doc_tag

DB_NAME = 'GameNet.db'

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

        elif sys.argv[1] == 'add_tag':
            name = input('Tag name: ')
            parent_id = int(input('Parent ID: '))
            print(add_tag(connection, name, parent_id))

        elif sys.argv[1] == 'add_document':
            sender_id = int(input('Sender ID: '))
            user_recipient_id = int(input('User recepient ID: '))
            group_recipient_id = int(input('Group recepient ID: '))
            access_password = getpass()
            header = input('Header: ')
            data = input('Data: ')
            print(add_document(connection, sender_id, user_recipient_id,
                  group_recipient_id, access_password,
                  header, data))

        elif sys.argv[1] == 'add_doc_tag':

            document_id = int(input('Document ID: '))
            tag_id = int(input('tag ID: '))
            print(add_doc_tag(connection, document_id, tag_id))
