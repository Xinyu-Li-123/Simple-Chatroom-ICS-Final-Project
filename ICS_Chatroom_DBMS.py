import sqlite3
import os
import time

import chat_utils as utils


class Chat_DBMS:
    """ This is the Database Management System of the ICS_Chatroom_Database"""
    def __init__(self):
        self.DB_NAME = utils.DB_NAME
        self.DB_PATH = utils.DB_PATH
        self.db = sqlite3.connect(self.DB_PATH)
        self.cursor = self.db.cursor()

    def __enter__(self):
        return Chat_DBMS()

    """
    Format for search
        sql = """"""
        self.cursor.execute(sql)
        return self.cursor.fetchone / fetchmany / fetchall
        
    Format for update
        sql = """""""
        self.cursor.execute(sql)
        self.db.commit()
    """
    def is_user_id_exist(self, user_id):
        sql = f"""SELECT * FROM users WHERE user_id='{user_id}'"""
        self.cursor.execute(sql)
        return bool(self.cursor.fetchone())

    def is_username_exist(self, username):
        sql = f"""SELECT * FROM users WHERE username='{username}'"""
        self.cursor.execute(sql)
        return bool(self.cursor.fetchone())

    def is_group_name_exist(self, group_name):
        sql = f"""SELECT * FROM groups WHERE group_name='{group_name}'"""
        self.cursor.execute(sql)
        return bool(self.cursor.fetchone())

    def is_group_id_exist(self, group_id):
        sql = f"""SELECT * FROM groups WHERE group_id='{group_id}'"""
        self.cursor.execute(sql)
        return bool(self.cursor.fetchone())

    def user_name2id(self, username):
        sql = f"""SELECT user_id FROM users WHERE username='{username}';"""
        self.cursor.execute(sql)
        user_id = self.cursor.fetchone()
        if user_id is not None:
            return user_id[0]
        return user_id

    def user_id2name(self, user_id):
        sql = f"""SELECT username FROM users WHERE user_id={user_id}"""
        self.cursor.execute(sql)
        username = self.cursor.fetchone()
        if username is not None:
            return username[0]

    def group_name2id(self, group_name):
        sql = f"""SELECT group_id FROM groups WHERE group_name='{group_name}';"""
        self.cursor.execute(sql)
        group_id = self.cursor.fetchone()
        if group_id is not None:
            return group_id[0]
        return group_id

    def group_id2name(self, group_id):
        sql = f"""SELECT group_name FROM groups WHERE group_id={group_id}"""
        self.cursor.execute(sql)
        group_name = self.cursor.fetchone()
        if group_name is not None:
            return group_name[0]


    def validate_login(self, username, password):
        sql = f"""SELECT user_id FROM users 
                  WHERE username='{username}'
                  AND password='{password}';"""
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        return bool(result)

    def create_user(self, username, password):
        # won't create user if username duplicates
        if self.is_username_exist(username):
            return False, f"Username: {username} has been registered!"

        sql = f"""INSERT INTO users (username, password)
                  VALUES ('{username}', '{password}');"""
        try:
            self.cursor.execute(sql)
            self.db.commit()
            print(f"[DATABASE] New user: {username} "
                  f"has been added to {self.DB_NAME}")
            return True, f"{username} has registered successfully."
        except sqlite3.OperationalError as e:
            print(f"[DATABASE_ERROR] {e}")
            return False, f"An error has occured in DBMS: {e}"

    def create_group(self, group_name):
        # if group_name is None:      # by default, group_name is the group_id
        #     self.cursor.execute("SELECT max(group_id) FROM groups")
        #     group_name = str(self.cursor.fetchone()[0])

        if self.is_group_name_exist(group_name):
            return False, f"group name: '{group_name}' has been used."
        sql=f"""INSERT INTO groups (group_name) VALUES ('{group_name}');"""
        try:
            self.cursor.execute(sql)
            self.db.commit()
            return True, f"group: '{group_name}' has been created."
        except sqlite3.OperationalError as e:
            print(f"[DATABASE_ERROR] {e}")
            return False, f"An error has occured in DBMS: {e}"

    def add_message(self, send_from, send_to, content):


        if not self.is_username_exist(send_from):
            return False, f"user: '{send_from}' does not exist."

        if not self.is_group_id_exist(send_to):
            return False, f"group #{send_to}' does not exist."

        send_from_id = self.user_name2id(send_from)

        if not self.is_user_in_group(send_from_id, send_to):
            return False, f"user: '{send_from}' is not in group #{send_to}"

        cur_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        send_from = self.user_name2id(send_from)

        # replace ' and " with ''
        content = content.replace("'", "''")
        content = content.replace("\"", "''")

        sql = f"""INSERT INTO messages (send_date, send_from, send_to, content)
                  VALUES ('{cur_time}', {send_from}, {send_to}, '{content}');"""

        try:
            self.cursor.execute(sql)
            self.db.commit()
            print(f"[DATABASE] A new message has been added:\n"
                  f"send date: {cur_time}\n"
                  f"send from: user  #{send_from}\n"
                  f"send to  : group #{send_to}\n"
                  f"content  : {content}\n")

            return True, "your message has been added to the database"
        except Exception as e:
            print(f"[DATABASE_ERROR] {e}")
            return False, f"An error has occured in DBMS: {e}"

    def join_group(self, username, group_id):
        if not self.is_username_exist(username):
            return False, f"user: '{username}' does not exist."
        user_id = self.user_name2id(username)

        if not self.is_group_id_exist(group_id):
            return False, f"group #{group_id} does not exist."

        if self.is_user_in_group(user_id, group_id):
            group_name = self.group_id2name(group_id)
            return False, f"user: '{username}' has already joined group: '{group_name}'."

        sql = f"""INSERT INTO in_group VALUES ({user_id}, {group_id});"""

        try:
            self.cursor.execute(sql)
            self.db.commit()
            return True, f"{username} has joined group #{group_id}"
        except Exception as e:
            print(f"[DATABASE ERROR] {e}")
            return False, f"Error: {e}"

    def is_user_in_group(self, user_id: int, group_id: int):
        """
        Can't validate if user_id or group_id exist!
        """
        sql = f"""SELECT * FROM in_group WHERE user_id={user_id} AND group_id={group_id}"""

        self.cursor.execute(sql)
        result = self.cursor.fetchone()

        if result:
            return True
        return False

    def leave_group(self, username, group_id):
        if not self.is_username_exist(username):
            return False, f"user: '{username}' does not exist."
        user_id = self.user_name2id(username)

        if not self.is_group_id_exist(group_id):
            return False, f"group #{group_id} does not exist."

        if not self.is_user_in_group(user_id, group_id):
            return False, f"user: '{username}' is not a member of group #{group_id}, thus can't leave this group."

        leave_group_sql = f"""DELETE FROM in_group WHERE user_id={user_id} AND group_id={group_id};"""
        delete_msg_sql = f"""DELETE FROM messages WHERE send_from={user_id} AND send_to={group_id};"""

        try:
            self.cursor.execute(leave_group_sql)
            self.cursor.execute(delete_msg_sql)
            self.db.commit()
            return True, f"{username} has leave group #{group_id}"
        except Exception as e:
            print(f"[DATABASE ERROR] {e}")
            return False, f"Error: {e}"

    def delete_account(self, username):
        pass

    def search(self, username, term):
        if not self.is_username_exist(username=username):
            return False, f"user: '{username}' does not exist."
        user_id = self.user_name2id(username)
        _, group_ids = self.list_groups_of_user(username)
        group_ids = tuple([g[0] for g in group_ids])

        sql=f"""SELECT send_date, send_from, send_to, content
                FROM messages 
                WHERE send_to IN {str(group_ids)}              
                AND content
                LIKE '%{term}%';"""
        print(sql)
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        print(result)
        result_str = []
        if result:
            for r in result:
                result_str.append(f"[{r[0]}] "
                                  f"in group #{r[2]}: {self.group_id2name(r[2])}\n"
                                  f"[{self.user_id2name(r[1])}] "
                                  f"{r[3]}")
        return True, result_str

    def show_users_in_group(self, group_id):
        sql = f"""SELECT user_id FROM in_group WHERE group_id={group_id};"""
        self.cursor.execute(sql)
        return self.cursor.fetchall()

    def load_history(self, username):
        if not self.is_username_exist(username):
            return False, f"user: '{username}' does not exist."
        user_id = self.user_name2id(username)

        sql = f"""SELECT groups.group_id, groups.group_name 
                  FROM groups, in_group 
                  WHERE in_group.user_id={user_id}
                  AND groups.group_id=in_group.group_id;"""
        self.cursor.execute(sql)
        return True, self.cursor.fetchall()

    def list_groups_of_user(self, username):
        if not self.is_username_exist(username):
            return False, f"user: '{username}' does not exist."
        user_id = self.user_name2id(username)
        sql=f"""SELECT group_id FROM in_group WHERE user_id={user_id};"""
        self.cursor.execute(sql)
        return True, self.cursor.fetchall()

    def list_users_in_group(self, group_id):
        if not self.is_group_id_exist(group_id):
            return False, f"group #{group_id} does not exist."
        sql=f"""SELECT user_id FROM in_group WHERE group_id={group_id}"""
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        if result:
            result = [self.user_id2name(g[0]) for g in result]

        return True, result

    # manually exit the database
    def close(self):
        self.db.commit()
        self.cursor.close()
        self.db.close()

    # exit using with statement
    def __exit__(self, *args, **kwargs):
        self.close()


class Test:
    def __init__(self):
        pass

    def test(self):
        with Chat_DBMS() as dbms:
            dbms.search()

if __name__ == "__main__":
    with Chat_DBMS() as dbms:
        dbms.show_all_users()
        # dbms.create_user("Cathy", "55555555")
        print(dbms.is_group_name_duplicated("test_grp"))
