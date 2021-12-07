import select
import threading
import json
import chat_utils as utils
import time
import socket
import indexer
import ICS_Chatroom_DBMS as DBMS


class Server:
    def __init__(self):
        self.new_clients = []  # list of new sockets of which the user id is not known
        self.logged_sock2name = {}
        self.all_sockets = []
        self.dbms = DBMS.Chat_DBMS()

        # start server
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.server.bind(utils.SERVER)
        self.server.listen(5)
        self.all_sockets.append(self.server)

        # poem database
        self.sonnet = indexer.PIndex("AllSonnets.txt")

    @property
    def logged_name2sock(self):
        d = {}
        for item in self.logged_sock2name.items():
            sock = item[0]
            name = item[1]
            if name is not None:
                d[name] = sock
        return d

    def new_client(self, sock):
        # add to all sockets and to new clients
        print('[NEW CONNECTION] new client...')
        sock.setblocking(0)
        self.new_clients.append(sock)
        self.all_sockets.append(sock)


    def login_or_register(self, sock, msg_from_user=None):
        # read the msg that should have login code plus username
        # for the convenience of coding, login and register are both handled in Server.login().
        try:
            if msg_from_user is None:
                # - is None means login_or_register is called in Server.run()
                # - not None means login_or_register is called in Server.handle_msg().
                # This if statement is added because a duplicated recv call from
                #       same socket will make the second recv return nothing
                msg_from_user = json.loads(utils.myrecv(sock))
            if utils.VERBOSE:
                print("[DEBUG]\t\tmessage received from client")
            if len(msg_from_user) > 0:
                msg_to_user = ""
                if msg_from_user["action"] == "login":
                    username = msg_from_user["username"]
                    password = msg_from_user["password"]
                    if sock not in self.logged_sock2name:       # update socket state if it's first attempt to login
                        self.new_clients.remove(sock)
                        self.logged_sock2name[sock] = None

                    if username in self.logged_sock2name.values():     # is duplicated login?
                        status = False
                        msg_to_user = f"Duplicated login attempt: {username} has already logged in!"
                        print(f"[LOGIN] Duplicated login attempt: {username} has already logged in!")
                    else:
                        if self.dbms.is_username_exist(username):           # is username registered?
                            if self.dbms.validate_login(username, password):    # is password correct?
                                status = True
                                msg_to_user = f"{username} has logged in successfully."

                                print(f"[LOGIN] {username} has logged in.")
                                self.logged_sock2name[sock] = username      # update the logged account on sock
                            else:
                                status = False
                                msg_to_user = f"Password incorrect!"
                        else:
                            status = False
                            msg_to_user = f"Username: {username} is not registered"

                    utils.mysend(sock, json.dumps(
                        {
                            "action": "login",
                            "status": status,
                            "username": username,
                            "message": msg_to_user
                        }
                    ))

                elif msg_from_user["action"] == "register":
                    username = msg_from_user["username"]
                    password = msg_from_user["password"]
                    if self.dbms.is_username_exist(username):
                        no_error = False
                        msg_to_user = f"Username: {username} has been used"
                        print(f"[ERROR] Username: {username} has been used")
                    else:
                        no_error, msg_to_user = self.dbms.create_user(username, password)
                        if no_error:
                            print(f"[REGISTER] {username} has registered.")
                        else:
                            print(f"[ERROR] [REGISTER] An error occurs when {username} attemps to register.")
                    utils.mysend(sock, json.dumps(
                        {"action": "register",
                         "status": no_error,
                         "username": username,
                         "password": password,
                         "message": msg_to_user}))

                elif msg_from_user["action"] == "exit":
                    # this happens when the user exit without ever logging in
                    self.logout(sock)
                    self.all_sockets.remove(sock)
                    sock.close()

                else:
                    print(f'[ERROR] Wrong code received: {msg_from_user}')

            else:  # client died unexpectedly
                self.logout(sock)

        except IndexError as e:
            print(e)
            print(f"[DISCONNECTION] an unlogged client has disconnected from the server.")
            self.all_sockets.remove(sock)


    def logout(self, sock):
        # remove sock from all lists
        try:
            username = self.logged_sock2name[sock]
            self.logged_sock2name[sock] = None
            if username is not None:
                print(f"[LOGOUT] {username} has logged out.")
            else:
                print(f"[DISCONNECTION] A socket has disconnected from the server: \n\t{sock}")
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False


    def handle_msg(self, from_sock):
        # read msg code
        msg_from_user = utils.myrecv(from_sock)
        if len(msg_from_user) > 0:

            msg_from_user = json.loads(msg_from_user)
            if msg_from_user["action"] == "login" or msg_from_user["action"] == "register":
                self.login_or_register(from_sock, msg_from_user=msg_from_user)

            elif msg_from_user["action"] == "poem":
                poem_idx = msg_from_user["index"]
                try:
                    poem_idx = int(poem_idx)
                    poem = "\n".join(self.sonnet.get_poem(poem_idx))
                    from_name = msg_from_user["send_from"]
                    print(f"[POEM QUERY] {from_name} searches for poem #{poem_idx}")

                    msg_to_user = json.dumps({"action": "poem",
                                              "index": poem_idx,
                                             "status": True,
                                             "result": poem})
                    utils.mysend(from_sock, msg_to_user)
                except:
                    msg_to_user = json.dumps({"action": "poem",
                                              "index": poem_idx,
                                             "status": False,
                                             "result": None})
                    utils.mysend(from_sock, msg_to_user)

            elif msg_from_user["action"] == "time":
                from_name = msg_from_user["send_from"]
                print(f"[TIME QUERY] {from_name} asking for server time.")
                ctime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                msg_to_user = json.dumps({"action": "time",
                                          "result": ctime})
                utils.mysend(from_sock, msg_to_user)  # @a: this is the Fricking PEER_MSGS in chat_client_class.py

            elif msg_from_user["action"] == "load_history":
                username = msg_from_user["send_from"]
                no_error, result = self.dbms.load_history(username)
                if no_error:
                    msg_to_user = json.dumps({"action": "load_history",
                                              "status": True,
                                              "result": result})
                else:
                    msg_to_user = json.dumps({"action": "load_history",
                                              "status": False,
                                              "message": result})
                utils.mysend(from_sock, msg_to_user)

            elif msg_from_user["action"] == "send_chat":
                if utils.VERBOSE:
                    print(f"[DEBUG]\t\t{msg_from_user}")
                send_from = msg_from_user["send_from"]
                send_to = msg_from_user["send_to"]
                msg = msg_from_user["message"].rstrip()
                no_error, result = self.dbms.list_users_in_group(send_to)
                if no_error:
                    msg_to_user = json.dumps({"action": "recv_chat",
                                              "send_from": send_from,
                                              "send_to": send_to,
                                              "message": msg})

                    for s in self.logged_sock2name:
                        if self.logged_sock2name[s] in result:
                            utils.mysend(s, msg_to_user)

                    if utils.VERBOSE:
                        print(f"[DEBUG]\t\tMessages send to all users in group #{send_to}")

                    self.dbms.add_message(send_from, send_to, msg)
                else:
                    print(f"[ERROR] fail to send message: \n{msg_from_user}"
                          f"because {result}")

            elif msg_from_user["action"] == "join_group":
                username = msg_from_user["send_from"]
                group_name = msg_from_user["group_name"]
                user_id = self.dbms.user_name2id(username)
                group_id = self.dbms.group_name2id(group_name)

                if not self.dbms.is_group_name_exist(group_name):
                    no_error = False
                    msg = f"group: '{group_name}' does not exist."
                else:
                    no_error, msg = self.dbms.join_group(username, group_id)

                utils.mysend(from_sock, json.dumps({"action": "join_group",
                                                    "status": no_error,
                                                    "group_name": group_name,
                                                    "group_id": group_id,
                                                    "message": msg}))

            elif msg_from_user["action"] == "create_group":
                group_name = msg_from_user["group_name"]

                if self.dbms.is_group_name_exist(group_name):       # group already exists
                    no_error = False
                    msg = f"group name: '{group_name}' has been used."
                else:
                    no_error, msg = self.dbms.create_group(group_name)

                utils.mysend(from_sock, json.dumps({"action": "create_group",
                                                    "status": no_error,
                                                    "group_name": group_name,
                                                    "message": msg}))

            elif msg_from_user["action"] == "search_chat_history":
                username = msg_from_user["send_from"]
                term = msg_from_user["term"]
                print(f"[CHAT HISTROY QUERY] Searching for '{term}' from the chatting history of user: {username}")
                no_error, result = self.dbms.search(username, term)

                if no_error:
                    utils.mysend(from_sock, json.dumps({"action": "search_chat_history",
                                                        "status": no_error,
                                                        "term": term,
                                                        "result": result,
                                                        "message": f"Search from chat history successfully"}))
                else:
                    utils.mysend(from_sock, json.dumps({"action": "search_chat_history",
                                                        "status": no_error,
                                                        "message": result}))
            elif msg_from_user['action'] == "leave_group":
                username = msg_from_user["send_from"]
                group_name = msg_from_user["group_name"]
                no_error, msg = self.dbms.delete_user_from_group(username, group_name)
                utils.mysend(from_sock, json.dumps({"action": "leave_group",
                                                    "status": no_error,
                                                    "group_name": group_name,
                                                    "message": msg}))

            elif msg_from_user['action'] == "logout":
                username = msg_from_user["send_from"]
                try:
                    no_error = self.logout(from_sock)
                    if no_error:
                        utils.mysend(from_sock, json.dumps(
                            {"action": "logout",
                             "status": True,
                             "message": f"{username} has logged out"}))
                    else:
                        utils.mysend(from_sock, json.dumps(
                            {"action": "logout",
                             "status": False,
                             "message": "logout fails for unknown reason."}))
                except Exception as e:
                    print(f"[ERROR] an error occurs during logging out: {e}")

            elif msg_from_user["action"] == "exit":
                self.logout(from_sock)
                self.all_sockets.remove(from_sock)
                from_sock.close()

        else:
            # client died unexpectedly
            self.logout(from_sock)


    # the mainloop
    def run(self):
        print('[Booting] starting server...')
        while True:
            try:
                read, write, error = select.select(self.all_sockets, [], [])
                print('[CHECKING] checking logged clients..')                      # handle messages from current clients
                for logc in self.logged_sock2name:
                    if logc in read:
                        self.handle_msg(logc)
                print('[CHECKING] checking new clients..')                         # new clients, login or register
                for newc in self.new_clients:
                    if newc in read:
                        self.login_or_register(newc)
                print('[CHECKING] checking for new connections..')                 # check potential connection
                if self.server in read:        # if server is readable, connect (i.e. append to new_client).
                    # new client request
                    sock, address = self.server.accept()
                    self.new_client(sock)

            except ValueError as e:
            # except Exception as e:
                print(e)
                print(f"[EXIT] Server has shut down.")
                break

    # shut_down() is a Failed attempt. I was trying to start a new thread for shutting
    #       down server from the commandline, but it doesn't work.
    # def shut_down(self):
    #     while True:
    #         try:
    #             input()
    #         except Exception as e:
    #             # for s in self.all_sockets:
    #             #     self.logout(s)
    #             print(e)
    #             self.server.close()
    #             print("[EXIT] Shutting down the server...")
    #             break

if __name__ == "__main__":
    myserver = Server()
    myserver.run()



