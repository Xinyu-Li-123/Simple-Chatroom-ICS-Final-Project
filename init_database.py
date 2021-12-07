import sqlite3
import chat_utils as utils

"""
This file is only used for initiate database. To run it, set utils.NEED_INIT to True,
then run it (remember to set it back to False after initiation on database.).

"""

if utils.NEED_INIT:

    init_table = ["""
    CREATE TABLE users(
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        -- user_id is in [100000, 199999]
        username TEXT UNIQUE,
        password TEXT
    );""",

    """
    -- add a test user
    INSERT INTO users 
    VALUES (100000, 'test_user', '11111111');
    """,

    """
    CREATE TABLE groups(
        group_id INTEGER PRIMARY KEY AUTOINCREMENT,
        -- group_id is in [200000, 299999]
        group_name TEXT DEFAULT 'Unnamed Group'
    );""",

    """
    -- add a test_group
    INSERT INTO groups 
    VALUES (200000, 'test_group');""",

    """
    CREATE TABLE messages(
        message_id INTEGER PRIMARY KEY AUTOINCREMENT,
        send_date TEXT,
        send_from INT
            REFERENCES users(user_id)
            ON DELETE CASCADE,
        send_to INT
            REFERENCES groups(group_id)
            ON DELETE CASCADE,
        content TEXT
    );""",

    """
    INSERT INTO messages 
    VALUES (300000, '2021-11-24 20:16:43', 100000, 200000, 'Hello world!');
    """,

    """
    CREATE TABLE in_group(
        user_id INTEGER,
        group_id INTEGER,
        FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
        FOREIGN KEY(group_id) REFERENCES groups(group_id) ON DELETE CASCADE
    );""",

    """
    INSERT INTO in_group 
    VALUES (100000, 200000);"""]

    db = sqlite3.connect(utils.DB_PATH)
    cursor = db.cursor()

    for sql in init_table:
        cursor.execute(sql)

    db.commit()
    cursor.close()
    db.close()