import time
import tkinter as tk
from tkinter import ttk, messagebox
import socket
import chat_utils as utils
import threading
import json
import sys


class Main_GUI(tk.Tk):
    def __init__(self):
        super(Main_GUI, self).__init__()
        self.client = Client(self)
        self.client.init_chat()

        self.LOGIN_IMG = tk.PhotoImage(file='res/login.png')
        self.POEM_IMG = tk.PhotoImage(file='res/poem.png')
        self.TIME_IMG = tk.PhotoImage(file='res/time.png')
        self.LOGOUT_IMG = tk.PhotoImage(file='res/logout.png')
        self.SEARCH_IMG = tk.PhotoImage(file='res/search.png')
        self.ADD_GROUP_IMG = tk.PhotoImage(file='res/join_group.png')

        self.font_normal = ["Comic Sans MS", 10]

    def exit(self):
        answer = messagebox.askquestion(title="Exit?",
                                        message="Are you sure you want to exit?")
        if answer == "yes":  # first logout, then exit
            if utils.VERBOSE:
                print(self.chat_frame.cache)
            self.client.exit()
            sys.exit()

    def app(self):
        """
        Put root in Main_GUI.app(), and configure other frames
        """
        self.title("ICS Chatroom")
        self.geometry("530x400")
        self.config(bg=utils.DEEPGREY)

        self.func_frame = Func_frame(self)
        self.func_frame.config(bg=utils.DEEPGREY)
        self.func_frame.grid(row=0, column=0, sticky='n')

        self.group_frame = Group_frame(self)
        self.group_frame.config(bg=utils.GREY)
        self.group_frame.grid(row=0, column=1, sticky="nswe")

        self.chat_frame = Chat_frame(self)
        self.chat_frame.config(bg=utils.WHITE)
        self.chat_frame.grid(row=0, column=2,
                             sticky="nswe")

        self.status_frame = Status_frame(self)
        self.status_frame.config(bg=utils.WHITE)
        self.status_frame.grid(row=0, column=0,
                               columnspan=2, sticky="nswe")

        self.rowconfigure(0, weight=1)
        self.columnconfigure(2, weight=1)

        self.group_frame.rowconfigure(0, weight=1)
        self.group_frame.rowconfigure(1, weight=1)
        self.group_frame.columnconfigure(0, weight=1)
        self.group_frame.columnconfigure(1, weight=1)

        self.chat_frame.rowconfigure(1, weight=1)
        self.chat_frame.columnconfigure(0, weight=3)

        self.leave_group_btn = Leave_group_button(self)
        self.leave_group_btn.grid(row=0, column=2, sticky="nswe", padx=10, pady=6)

        self.status_frame.columnconfigure(0, weight=1)
        self.status_frame.columnconfigure(1, weight=1)

        # an easter egg :)
        self.bind("<|><t><h>", lambda e: f"{self.chat_frame.chat_box.config(state=tk.NORMAL)}"
                                      f"{self.chat_frame.chat_box.insert('end', 'ᗜˬᗜ ')}"
                                      f"{self.chat_frame.chat_box.config(state=tk.DISABLED)}")

        self.protocol("WM_DELETE_WINDOW", self.exit)


        self.chat_frame.switch_to(utils.SYS_GRP_ID)


class Client:
    def __init__(self, root: Main_GUI):
        self.state = utils.S_OFFLINE
        self.name = None
        self.root = root
        self.group_count = 0

    def init_chat(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        svr = utils.SERVER
        self.socket.connect(svr)
        new_thread = threading.Thread(target=self.receive_msg_in_new_thread)
        new_thread.start()

    def login(self, name, password):
        if self.state == utils.S_OFFLINE:
            if name.isspace() or password.isspace():                # if name or password is empty
                self.root.chat_frame.new_msg.set(new_content="[SYSTEM] Login fail: Username and password can't be empty!",
                                                 group_id=utils.SYS_GRP_ID)
                self.root.chat_frame.put_up_new_msg()
            else:
                msg_to_server = json.dumps({"action": "login",
                                  "username": name,
                                  "password": password})

                utils.mysend(self.socket, msg_to_server)
                if utils.VERBOSE:
                    print("message send in login")
                    print(msg_to_server)
        else:
            self.root.chat_frame.new_msg.set(new_content=f"[SYSTEM] You have already logged in as: {self.name}",
                                             group_id=utils.SYS_GRP_ID)
            self.root.chat_frame.put_up_new_msg()


    def register(self, name, password):
        if self.state != utils.S_OFFLINE:       # if user has already logged in
            self.root.chat_frame.new_msg.set(new_content="[SYSTEM] You have already logged in as: {self.name}",
                                             group_id=utils.SYS_GRP_ID)
            self.root.chat_frame.put_up_new_msg()
        else:
            if name.isspace() or password.isspace():                # if name is empty
                self.root.chat_frame.new_msg.set(new_content="[SYSTEM] Register fail: Username and password can't be empty!",
                                                 group_id=utils.SYS_GRP_ID)
                self.root.chat_frame.put_up_new_msg()
            else:
                msg = json.dumps({"action": "register",
                                  "username": name,
                                  "password": password})

                utils.mysend(self.socket, msg)
                if utils.VERBOSE:
                    print(f"message send in Client.register():\n{msg}")

    def load_history(self):
        if self.state == utils.S_LOGGEDIN:
            msg = json.dumps({
                "action": "load_history",
                "send_from": self.name
            })
            utils.mysend(self.socket, msg)

    def clear_history(self):
        # clear history of previous user
        self.group_count = 0
        self.root.group_frame.clear_history()
        # clear groups cache except for system group
        self.root.chat_frame.cache = {
            utils.SYS_GRP_ID: self.root.chat_frame.cache[utils.SYS_GRP_ID]
        }

    def logout(self):
        if self.state != utils.S_OFFLINE:
            msg = json.dumps({"action": "logout",
                              "send_from": self.name})
            utils.mysend(self.socket, msg)

    def exit(self):
        msg = json.dumps({"action": "exit",
                          "send_from": self.name})
        utils.mysend(self.socket, msg)

    def get_time(self):
        msg_json = json.dumps({"action": "time",
                               "send_from": self.name})
        utils.mysend(self.socket, msg_json)

    def get_peom(self, poem_idx):
        try:
            if int(poem_idx) > 0:
                msg_json = json.dumps({"action": "poem",
                                       "send_from": self.name,
                                       "index": poem_idx})
                utils.mysend(self.socket, msg_json)
            else:
                self.root.chat_frame.new_msg.set(new_content="[SYSTEM] Poem index must be a positive integer!",
                                                 group_id=utils.SYS_GRP_ID)
                self.root.chat_frame.put_up_new_msg()
        except ValueError:
            self.root.chat_frame.new_msg.set(new_content="[SYSTEM] Poem index must be a positive integer!",
                                             group_id=utils.SYS_GRP_ID)
            self.root.chat_frame.put_up_new_msg()

    def join_group(self, group_name):
        msg_json = json.dumps({
            "action": "join_group",
            "send_from": self.name,
            "group_name": group_name})
        utils.mysend(self.socket, msg_json)


    def create_group(self, group_name):
        msg_json = json.dumps({
            "action": "create_group",
            "group_name": group_name})
        utils.mysend(self.socket, msg_json)


    def chat(self, message, group_id):
        msg_json = json.dumps({"action": "send_chat",
                               "send_from": self.name,
                               "send_to": group_id,
                               "message": message})
        utils.mysend(self.socket, msg_json)
        if utils.VERBOSE:
            print("chat message send to server.")

    def search_chat_history(self, term: str):
        msg_json = json.dumps({"action": "search_chat_history",
                               "send_from": self.name,
                               "term": term})
        utils.mysend(self.socket, msg_json)

    def leave_group(self, group_name: str):
        msg_json = json.dumps({"action": "leave_group",
                               "send_from": self.name,
                               "group_name": group_name})
        utils.mysend(self.socket, msg_json)

    # a typical application is:
    # send_msg(msg)
    # result = receive_msg()
    def receive_msg_in_new_thread(self):
        while True:
            msg_json = utils.myrecv(self.socket)
            if not msg_json:        # if msg_json is empty
                print("Disconnected")
                break
            msg_from_server = json.loads(msg_json)

            if utils.VERBOSE:
                print('msg_from_server: ' + str(msg_from_server))


            if msg_from_server["action"] == "login":

                if msg_from_server["status"] == True:      # login successfully
                    self.state = utils.S_LOGGEDIN
                    self.name = msg_from_server["username"]
                    self.root.status_frame.client_state = self.root.client.state
                    self.root.status_frame.client_name = self.root.client.name
                    self.root.func_frame.popup_login_frame.destroy()
                    self.load_history()  # if login succeed, load user's history

                else:
                    self.root.func_frame.username_ety.delete(0, "end")
                    self.root.func_frame.password_ety.delete(0, "end")
                    self.root.func_frame.username_ety.focus()

                msg = msg_from_server["message"]
                self.root.chat_frame.new_msg.set(new_content="[SYSTEM] " + msg,
                                                 group_id=utils.SYS_GRP_ID)
                self.root.chat_frame.put_up_new_msg()


            elif msg_from_server["action"] == "register":

                msg = msg_from_server["message"]
                self.root.chat_frame.new_msg.set(new_content="[SYSTEM] " + msg,
                                                 group_id=utils.SYS_GRP_ID)
                self.root.chat_frame.put_up_new_msg()

                if msg_from_server["status"] is True:  # if register succeed, login
                    name = msg_from_server["username"]
                    password = msg_from_server["password"]
                    self.login(name, password)

            elif msg_from_server["action"] == "load_history":
                no_error = msg_from_server["status"]
                if no_error:
                    result = msg_from_server["result"]
                    self.root.group_frame.load_history(result)
                else:
                    msg = msg_from_server["message"]
                    self.root.chat_frame.new_msg.set(new_content='[SYSTEM] ' + msg,
                                                     group_id=utils.SYS_GRP_ID)

            elif msg_from_server["action"] == "time":
                cur_time = msg_from_server["result"]
                self.root.chat_frame.new_msg.set(new_content=f"[SYSTEM] The current server time is {cur_time}.",
                                                 group_id=utils.SYS_GRP_ID)
                self.root.chat_frame.put_up_new_msg()
                self.root.chat_frame.switch_to(utils.SYS_GRP_ID)

            elif msg_from_server["action"] == "poem":
                no_error = msg_from_server["status"]
                poem_idx = msg_from_server["index"]
                if no_error:
                    self.root.chat_frame.new_msg.set(new_content=f"[SYSTEM] Poem #{poem_idx} retrieved successfully.",
                                                 group_id=utils.SYS_GRP_ID)
                    self.root.chat_frame.put_up_new_msg()
                    poem = msg_from_server["result"]
                    self.root.func_frame.popup_show_poem(poem)
                else:
                    self.root.chat_frame.new_msg.set(new_content=f"[SYSTEM] Poem #{poem_idx} not found in the sonnet database..",
                                                 group_id=utils.SYS_GRP_ID)
                    self.root.chat_frame.put_up_new_msg()
                self.root.chat_frame.switch_to(utils.SYS_GRP_ID)


            elif msg_from_server["action"] == "recv_chat":
                send_from = msg_from_server["send_from"]
                group_id = msg_from_server["send_to"]
                new_msg = msg_from_server['message']
                self.root.chat_frame.new_msg.set(new_content=new_msg,
                                                 group_id=group_id,
                                                 send_from=send_from)
                self.root.chat_frame.put_up_new_msg()

            elif msg_from_server["action"] == "create_group":
                no_error  = msg_from_server["status"]
                group_name = msg_from_server["group_name"]
                msg = '[SYSTEM] ' + msg_from_server["message"]

                self.root.chat_frame.new_msg.set(new_content=msg,
                                                 group_id=utils.SYS_GRP_ID)
                self.root.chat_frame.put_up_new_msg()

                if no_error:
                    self.join_group(group_name)

            elif msg_from_server["action"] == "join_group":
                no_error = msg_from_server["status"]
                msg = f"[SYSTEM] {msg_from_server['message']}"
                group_id = msg_from_server["group_id"]
                group_name = msg_from_server["group_name"]

                self.root.chat_frame.new_msg.set(new_content=msg,
                                                 group_id=utils.SYS_GRP_ID)
                self.root.chat_frame.put_up_new_msg()

                if no_error:
                    self.root.group_frame.put_up_group(group_id, group_name)
                    self.root.group_frame.popup_join_group_frame.destroy()

            elif msg_from_server["action"] == "search_chat_history":
                no_error = msg_from_server["status"]
                msg = "[SYSTEM] " + msg_from_server["message"]
                self.root.chat_frame.new_msg.set(new_content=msg,
                                                 group_id=utils.SYS_GRP_ID)
                self.root.chat_frame.put_up_new_msg()

                if no_error:
                    term = msg_from_server["term"]
                    result = msg_from_server["result"]
                    self.root.group_frame.popup_search_result(term, result)

            elif msg_from_server["action"] == "leave_group":
                no_error = msg_from_server["status"]
                group_name = msg_from_server["group_name"]
                msg = '[SYSTEM] ' + msg_from_server["message"]
                if no_error:
                    group_id = self.root.group_frame.group_name2id[group_name]

                    self.root.chat_frame.switch_to(utils.SYS_GRP_ID)
                    self.root.group_frame.group_list_dict[group_name].destroy()

                    self.root.group_frame.group_list_dict.pop(group_name)
                    self.root.group_frame.group_name2id.pop(group_name)
                    self.root.group_frame.group_id2name.pop(group_id)

                self.root.chat_frame.new_msg.set(new_content=msg,
                                                 group_id=utils.SYS_GRP_ID)
                self.root.chat_frame.put_up_new_msg()

            elif msg_from_server["action"] == "logout":
                if msg_from_server["status"]:
                    self.state = utils.S_OFFLINE
                    self.name = None
                    self.root.status_frame.client_state = utils.S_OFFLINE
                    self.root.status_frame.client_name = "    "

                    self.root.chat_frame.chat_box.delete(0, 'end')
                    self.clear_history()

                self.root.chat_frame.new_msg.set(new_content="[SYSTEM] " + msg_from_server["message"],
                                                 group_id=utils.SYS_GRP_ID)
                self.root.chat_frame.put_up_new_msg()

            elif msg_from_server["action"] == "exit":
                return None, None

            else:
                return False, ""
        time.sleep(utils.CHAT_WAIT)


class New_message:              # the newest message to be displayed on the screen
    """
    The idea is that there is always one and only one piece of new message, and it always directly
        comes from the SYSTEM (even if you are chatting with other users).
    So, we can implement different functinolity by **updating New_message** accordingly, with different other responses.
    """
    def __init__(self):
        self.__content = "NULL"
        self.__group_id = utils.SYS_GRP_ID
        self.__send_from = "NULL"

    def get(self):
        return self.__content, self.__group_id, self.__send_from

    def set(self, new_content, group_id=utils.SYS_GRP_ID, send_from=None):  # None is msg send from system
        self.__content = new_content
        self.__group_id = group_id
        self.__send_from = send_from

    def clear(self):
        self.__content = "NULL"
        self.__group_id = utils.SYS_GRP_ID
        self.__send_from = "NULL"

class Leave_group_button(tk.Button):
    def __init__(self, root: Main_GUI):
        self.root = root
        super(Leave_group_button, self).__init__(
            self.root.chat_frame,
            text='leave',
            width=5, height=1,
            bg=utils.WHITE,
            relief='flat',
            font=utils.FONT_LARGE
        )
        print("BUTTON LOADED")
        self.set_command()

    def set_command(self):
        if self.root.chat_frame.cur_group_id == utils.SYS_GRP_ID or self.root.chat_frame.cur_group_id == -1:
            # you can't leave the system group
            self.config(command=lambda: "",        # do nothing
                        fg=utils.WHITE, bg=utils.WHITE,
                        relief='flat')
        else:
            self.config(state=tk.NORMAL)
            # suspicious
            self.config(command=self.leave_group,
                        fg=utils.DEEPGREY, bg=utils.WHITE,
                        relief='raised')

            if utils.VERBOSE:
                print(f"Inside leave_group_btn: leave group name: {self.root.group_frame.group_id2name[self.root.chat_frame.cur_group_id]}")

    def leave_group(self):
        group_name = self.root.group_frame.group_id2name[self.root.chat_frame.cur_group_id]
        answer = messagebox.askquestion(title="Exit?",
                                        message=f"Are you sure you want to leave group: '{group_name}'?"
                                                f"\n(All the messages you sent in this group will be deleted)")
        if answer == "yes":
            self.root.chat_frame.leave_group(group_name)


class Group_button(tk.Button):
    def __init__(self, root: Main_GUI, group_id: int, group_name: str, chat_frame):

        if not isinstance(group_id, int):
            raise TypeError(f"group_id of Group_Button must be int (not {type(group_id)})")
        if not isinstance(group_name, str):
            raise TypeError(f"group_name of Group_Button must be str (not {type(group_name)})")

        self.root = root
        self.group_id = group_id

        # reformat group_name
        self.group_name = ""
        for i in range(len(group_name)):
            if i % 20 or i == 0:
                self.group_name += group_name[i]
            else:
                self.group_name += '\n'

        text=f"#{str(group_id)}\n{group_name}"
        super(Group_button, self).__init__(self.root.group_frame.group_list_frame,
                                           text=text,
                                           command=lambda:f"{self.root.chat_frame.switch_to(group_id=group_id)}",
                                           bg=utils.GREY,
                                           fg=utils.WHITE,
                                           font=utils.FONT_LARGE,
                                           relief="flat"
                                           )


class Group_frame(tk.Frame):
    def __init__(self, root: Main_GUI):
        super(Group_frame, self).__init__(root)
        self.root = root

        self.group_list_frame = tk.Frame(self, bg=utils.GREY)
        self.group_list_frame.grid(row=0, column=0, columnspan=2, sticky="n")
        self.group_list = []
        self.group_list_dict = {}       # name2btn
        self.group_id2name = {}
        self.group_name2id = {}

        # system info
        tk.Button(self.group_list_frame,
                      text="System",
                      command=lambda: self.root.chat_frame.switch_to(utils.SYS_GRP_ID),
                      bg=utils.GREY,
                      fg=utils.WHITE,
                      font=utils.FONT_LARGE,
                      relief="flat").grid(row=0, column=0, sticky="new")

        search_btn = tk.Button(self,
                               image=self.root.SEARCH_IMG,
                               bg=utils.WHITE,
                               command=self.popup_search_chat)
        search_btn.grid(row=1, column=0,
                        padx=2, pady=4,
                        ipadx=2, ipady=2,
                        sticky="swe")

        join_group_btn = tk.Button(self,
                                   image=self.root.ADD_GROUP_IMG,
                                   bg=utils.WHITE,
                                   command=self.popup_join_group)
        join_group_btn.grid(row=1, column=1,
                            padx=2, pady=4,
                            ipadx=2, ipady=2,
                            sticky="swe")

        self.group_list_frame.columnconfigure(0, weight=1)

    def load_history(self, history):
        if utils.VERBOSE:
            print(f"history: {history}")
        for h in history:
            self.put_up_group(group_id=h[0],
                              group_name=h[1])
        if utils.VERBOSE:
            print("All history are loaded")

    def put_up_group(self, group_id, group_name):
        if self.root.client.group_count > utils.MAX_GROUP_NUM:
            self.root.chat_frame.new_msg.set(new_content="[SYSTEM] You can only join at most 10 groups!",
                                                group_id=utils.SYS_GRP_ID)
            self.root.chat_frame.put_up_new_msg()
        else:
            self.root.chat_frame.cache[group_id] = f"Group #{group_id}: {group_name}"
            btn = Group_button(root=self.root,
                               group_id=group_id,
                               group_name=group_name,
                               chat_frame=self.root.chat_frame)
            btn.grid(row=1+self.root.client.group_count,
                     column=0,
                     sticky="nwe")
            self.group_list.append(btn)
            if utils.VERBOSE:
                print(self.group_list_dict, self.group_id2name, self.group_name2id)
            if group_name not in self.group_list_dict:
                self.group_list_dict[group_name] = btn
                self.group_id2name[group_id] = group_name
                self.group_name2id[group_name] = group_id
            else:
                raise Exception("How is this possible ?!")

            self.root.client.group_count += 1
            if utils.VERBOSE:
                print(f"Group #{group_id}: {group_name} put up.")
            self.group_list_dict[group_name] = btn
            self.group_id2name[group_id] = group_name
            self.group_name2id[group_name] = group_id

    def clear_history(self):
        # clear history of previous users
        # for b in self.group_list:
        for b in self.group_list_dict.values():
            b.destroy()
        # self.group_list = []
        self.group_list_dict = {}
        # switch to system chat_box
        self.root.chat_frame.switch_to(utils.SYS_GRP_ID)

    def popup_join_group(self):
        # create new group or join existing group
        if self.root.client.state == utils.S_OFFLINE:
            self.root.chat_frame.new_msg.set(new_content=f"[SYSTEM] Please log in first",
                                             group_id=utils.SYS_GRP_ID)
            self.root.chat_frame.put_up_new_msg()
            return

        self.popup_join_group_frame = tk.Toplevel(self, bg=utils.GREY)
        self.popup_join_group_frame.geometry("270x80")
        self.popup_join_group_frame.title("Join Group")
        self.popup_join_group_frame.focus()

        tk.Label(self.popup_join_group_frame,
                 text="Group Name: ",
                 bg=utils.GREY,
                 fg=utils.WHITE,
                 font=utils.FONT_LARGE).grid(row=0, column=0)

        self.group_name_ety = tk.Entry(self.popup_join_group_frame,
                                       font=utils.FONT_LARGE)
        self.group_name_ety.grid(row=0, column=1)
        self.group_name_ety.focus()

        join_group_btn = tk.Button(self.popup_join_group_frame,
                                   text="Join",
                                   bg=utils.GREY,
                                   fg=utils.WHITE,
                                   font=utils.FONT_LARGE,
                                   command=lambda: f"{self.join_group(self.group_name_ety.get())}"
                                                   f"{self.group_name_ety.delete(0, tk.END)}")
        join_group_btn.grid(row=2, column=1, ipadx=20)

        create_group_btn = tk.Button(self.popup_join_group_frame,
                                  text="Create",
                                  bg=utils.GREY,
                                  fg=utils.WHITE,
                                  font=utils.FONT_LARGE,
                                  command=lambda: self.create_group(self.group_name_ety.get()))
        create_group_btn.grid(row=2, column=0)

        for w in self.popup_join_group_frame.winfo_children():
            w.grid(padx=4)
            w.grid(pady=2)

    def join_group(self, group_name: str):
        if self.root.client.state == utils.S_LOGGEDIN:
            if group_name in self.root.chat_frame.cache:    # user has already join this group
                self.root.chat_frame.new_msg.set(new_content="[SYSTEM] You are already in group: {group_name}",
                                                 group_id=utils.SYS_GRP_ID)
                self.root.chat_frame.put_up_new_msg()
            elif group_name.isspace():
                self.root.chat_frame.new_msg.set(new_content="[SYSTEM] Group name can't be empty.",
                                                 group_id=utils.SYS_GRP_ID)
                self.root.chat_frame.put_up_new_msg()
            else:
                self.root.client.join_group(group_name)

    def create_group(self, group_name: str):
        if self.root.client.state == utils.S_LOGGEDIN:
            if group_name.isspace():
                self.root.chat_frame.new_msg.set(new_content="[SYSTEM] Group name can't be empty.",
                                                 group_id=utils.SYS_GRP_ID)
                self.root.chat_frame.put_up_new_msg()
            else:
                self.root.client.create_group(group_name)

    def popup_search_result(self, term, result):
        self.popup_search_result_frame = tk.Toplevel(self, bg=utils.WHITE)
        self.popup_search_result_frame.geometry("600x300")
        self.popup_search_result_frame.title("Search Result")
        self.popup_search_result_frame.focus()
        self.popup_search_result_frame.rowconfigure(0, weight=1)
        self.popup_search_result_frame.columnconfigure(0, weight=1)

        result_box = tk.Text(self.popup_search_result_frame,
                             fg=utils.BLACK,
                             bg=utils.WHITE,
                             font=utils.FONT_NORMAL
                             )

        result_box.grid(row=0, column=0, sticky="nswe")

        disp_result = f"[CHAT HISTORY SEARCH RESULT] We found {len(result)} chats that contains the term '{term}'\n"
        for r in result:
            disp_result += r + '\n'

        result_box.insert(tk.END, disp_result)
        result_box.config(state=tk.DISABLED)

        yscroll = ttk.Scrollbar(self.popup_search_result_frame,
                                orient="vertical",
                                command=result_box.yview)
        yscroll.grid(row=0, column=1, sticky="nse")

        for w in self.popup_search_result_frame.winfo_children():
            w.grid(padx=4)


    def popup_search_chat(self):
        if self.root.client.state != utils.S_LOGGEDIN:
            self.root.chat_frame.new_msg.set(new_content="[SYSTEM] Please log in first.",
                                             group_id=utils.SYS_GRP_ID)
            self.root.chat_frame.put_up_new_msg()
            return

        self.popup_search_chat_frame = tk.Toplevel(self, bg=utils.GREY)
        self.popup_search_chat_frame.geometry("250x120")
        self.popup_search_chat_frame.title("Search in Chat History")
        self.popup_search_chat_frame.focus()
        self.popup_search_chat_frame.rowconfigure(0, weight=1)
        self.popup_search_chat_frame.columnconfigure(0, weight=1)

        tk.Label(self.popup_search_chat_frame,
                  text="Enter search term",
                 fg=utils.WHITE,
                 bg=utils.GREY,
                 font=utils.FONT_LARGE).grid(row=0,column=0,columnspan=2,sticky="nwe")
        search_term = tk.StringVar()
        search_term_entry = tk.Entry(self.popup_search_chat_frame,
                                     textvariable=search_term,
                                     fg=utils.BLACK,
                                     bg=utils.WHITE,
                                     font=utils.FONT_NORMAL)
        search_term_entry.grid(row=1, column=0, sticky="nwe")
        search_term_entry.focus()

        tk.Button(self.popup_search_chat_frame,
                   text="Search",
                  fg=utils.WHITE,
                  bg=utils.GREY,
                  font=utils.FONT_LARGE,
                   command=lambda: f"{self.search_chat_history(search_term.get())}"
                                   f"{search_term_entry.delete(0, 'end')}")

        for w in self.popup_search_chat_frame.winfo_children():
            w.grid(padx=4, pady=4)


    def search_chat_history(self, keyword: str):
        if not keyword or keyword.isspace():        # if input is nothing or space
            self.root.chat_frame.new_msg.set(new_content="[SYSTEM] Keyword can't be empty.",
                                             group_id=utils.SYS_GRP_ID)
            self.root.chat_frame.put_up_new_msg()
        else:
            self.root.client.search_chat_history(keyword)


class Func_frame(tk.Frame):
    def __init__(self, root: Main_GUI):
        super(Func_frame, self).__init__(root)
        self.root = root

        # log_in
        self.login_btn = tk.Button(self,
                                   image=self.root.LOGIN_IMG,
                                   command=self.popup_login,
                                   bg=utils.WHITE)
        self.login_btn.grid(row=0, column=0, padx=4, pady=4,
                            ipadx=2, ipady=2)

        # get_poem
        self.poem_btn = tk.Button(self,
                                  image=self.root.POEM_IMG,
                                  command=self.popup_get_poem,
                                  bg=utils.WHITE)
        self.poem_btn.grid(row=1, column=0, padx=4, pady=4,
                            ipadx=2, ipady=2)

        # get_time
        self.time_btn = tk.Button(self,
                                  image=self.root.TIME_IMG,
                                  command=self.get_time,
                                  bg=utils.WHITE)
        self.time_btn.grid(row=2, column=0, padx=4, pady=4,
                            ipadx=2, ipady=2)


        # logout
        self.logout_btn = tk.Button(self,
                                    image=self.root.LOGOUT_IMG,
                                    command=self.logout,
                                    bg=utils.WHITE)
        self.logout_btn.grid(row=3, column=0, padx=4, pady=4,
                            ipadx=2, ipady=2)

    def register(self, name: str, password: str):
        if not name.isspace() and not password.isspace():
            self.root.client.register(name, password)

    def login(self, name: str, password: str):
        self.root.client.login(name, password)

    def get_time(self):
        if self.root.client.state == utils.S_OFFLINE:
            self.root.chat_frame.new_msg.set(new_content="[SYSTEM] Please log in first.",
                                             group_id=utils.SYS_GRP_ID)
            self.root.chat_frame.put_up_new_msg()
        else:
            self.root.client.get_time()

    def get_poem(self, poem_idx):
        self.root.client.get_peom(poem_idx)

    def popup_show_poem(self, poem):
        """
        popup a window that shows the poem (poem is retrieved from the SYSTEM)
        """
        self.popup_show_poem_frame = tk.Toplevel(self, bg=utils.GREY)
        self.popup_show_poem_frame.geometry("400x600")
        self.popup_show_poem_frame.title("Search Result")
        self.popup_show_poem_frame.focus()
        self.popup_show_poem_frame.rowconfigure(0, weight=1)
        self.popup_show_poem_frame.columnconfigure(0, weight=1)

        poem_display_text = tk.Text(self.popup_show_poem_frame,
                                    fg=utils.BLACK,
                                    bg=utils.WHITE,
                                    font=utils.FONT_NORMAL)
        poem_display_text.grid(row=0, column=0, sticky="nswe")

        for w in self.popup_show_poem_frame.winfo_children():
            w.grid(padx=4)

        if poem is not None:
            poem_display_text.insert(tk.END, poem)
            poem_display_text.config(state=tk.DISABLED)
            self.popup_get_poem_frame.destroy()
        else:
            self.popup_show_poem_frame.destroy()

    def popup_get_poem(self):
        """
        popup a window that asks for the poem index.
        """
        if self.root.client.state == utils.S_OFFLINE:
            self.root.chat_frame.new_msg.set(new_content="[SYSTEM] Please log in first.",
                                             group_id=utils.SYS_GRP_ID)
            self.root.chat_frame.put_up_new_msg()
        else:
            self.popup_get_poem_frame = tk.Toplevel(self, bg=utils.GREY)
            self.popup_get_poem_frame.geometry("270x80")
            self.popup_get_poem_frame.title("Poem Database")
            self.popup_get_poem_frame.focus()
            self.popup_get_poem_frame.rowconfigure(0, weight=1)
            self.popup_get_poem_frame.columnconfigure(0, weight=1)

            tk.Label(self.popup_get_poem_frame,
                     text="Enter the index number of the poem",
                     fg=utils.WHITE,
                     bg=utils.GREY,
                     font=utils.FONT_LARGE).grid(row=0,
                                                  column=0,
                                                  columnspan=2,
                                                  sticky="nwe")
            poem_idx = tk.StringVar()
            poem_idx_entry = tk.Entry(self.popup_get_poem_frame,
                                      textvariable=poem_idx,
                                      fg=utils.BLACK,
                                      bg=utils.WHITE,
                                      font=utils.FONT_LARGE)
            poem_idx_entry.grid(row=1, column=0, sticky="nwe")
            poem_idx_entry.focus()

            tk.Button(self.popup_get_poem_frame,
                       text="Get Poem",
                       fg=utils.BLACK,
                       bg=utils.WHITE,
                       font=utils.FONT_LARGE,
                       command=lambda: f"{self.get_poem(poem_idx.get())}"
                                       f"{poem_idx_entry.delete(0, 'end')}").grid(row=1, column=1, sticky="nwe")

            for w in self.popup_get_poem_frame.winfo_children():
                w.grid(padx=4)

    def popup_login(self):
        if self.root.client.state != utils.S_OFFLINE:
            self.root.chat_frame.new_msg.set(new_content=f"[SYSTEM] You have already logged in as: {self.root.client.name}",
                                             group_id=utils.SYS_GRP_ID)
            self.root.chat_frame.put_up_new_msg()
            return

        self.popup_login_frame = tk.Toplevel(self, bg=utils.GREY)
        self.popup_login_frame.geometry("270x120")
        self.popup_login_frame.title("Login")
        self.popup_login_frame.focus()

        # username label & entry
        tk.Label(self.popup_login_frame,
                 text="Username: ",
                 bg=utils.GREY,
                 fg=utils.WHITE,
                 font=utils.FONT_LARGE).grid(row=0, column=0, sticky="nswe", padx=4, pady=3)

        self.username_ety = tk.Entry(self.popup_login_frame,
                                     font=utils.FONT_NORMAL)
        self.username_ety.grid(row=0, column=1, sticky="nsw", padx=4, pady=3)

        # password label & entry
        tk.Label(self.popup_login_frame,
                 text="Password: ",
                 bg=utils.GREY,
                 fg=utils.WHITE,
                 font=utils.FONT_LARGE).grid(row=1, column=0, sticky="nswe", padx=4, pady=2)

        self.password_ety = tk.Entry(self.popup_login_frame,
                                     font=utils.FONT_NORMAL,
                                     show="*")
        self.password_ety.grid(row=1, column=1, sticky="nswe", padx=4, pady=2)

        self.username_ety.focus()

        login_btn = tk.Button(self.popup_login_frame,
                               text="Login",
                               bg=utils.GREY,
                               fg=utils.WHITE,
                               font=utils.FONT_LARGE,
                               command=lambda: self.login(self.username_ety.get(),
                                                          self.password_ety.get()))
        login_btn.grid(row=2, column=1, sticky="ns", padx=4, pady=2, ipadx=20)

        register_btn = tk.Button(self.popup_login_frame,
                                  text="Register",
                                  bg=utils.GREY,
                                  fg=utils.WHITE,
                                  font=utils.FONT_LARGE,
                                  command=lambda: self.register(self.username_ety.get(),
                                                                self.password_ety.get()))
        register_btn.grid(row=2, column=0, sticky="ns", padx=4, pady=2)


    def logout(self):
        if self.root.client.state == utils.S_OFFLINE:  # if not logged in
            self.root.chat_frame.new_msg.set(new_content="[SYSTEM] You haven't logged in yet!",
                                             group_id=utils.SYS_GRP_ID)
            self.root.chat_frame.put_up_new_msg()
        else:
            self.root.client.logout()

class Chat_frame(tk.Frame):
    def __init__(self, root: Main_GUI):
        super(Chat_frame, self).__init__(root)

        self.root = root
        # utils.SYS_GRP_ID is the id of system
        self.cur_group_id = -1      # this is to initalize chat_box to system chat_box
        # history is volatile
        self.cache = {utils.SYS_GRP_ID: "System"}
        self.new_msg = New_message()



        self.chat_box = tk.Text(self, 
                                bg=utils.WHITE,
                                fg=utils.BLACK,
                                bd=2)
        self.chat_box.grid(row=1, column=0,
                           columnspan=3, sticky="nswe")
        self.chat_box.config(state=tk.DISABLED,
                             highlightbackground = utils.BLACK,
                             font = utils.FONT_NORMAL)

        yscroll = ttk.Scrollbar(self,
                                orient="vertical",
                                command=self.chat_box.yview)
        yscroll.grid(row=1, column=2, sticky="nse")

        self.chat_entry = tk.Text(self, height=3,
                                   bg=utils.WHITE,
                                   fg=utils.BLACK,
                                   bd=2)
        self.chat_entry.grid(row=2, column=0, columnspan=2, sticky="nswe")
        self.chat_entry.config(highlightbackground=utils.BLACK,
                               font=utils.FONT_NORMAL)


        self.send_msg_btn = tk.Button(self, text="send",
                                      width=5, height=2,
                                      bg=utils.WHITE,
                                      relief='raised',
                                      font=utils.FONT_LARGE,
                                      command=lambda: f"{self.chat(self.chat_entry.get('1.0', tk.END),self.cur_group_id)}"
                                                      f"{self.chat_entry.delete('1.0', tk.END)}")

        self.send_msg_btn.grid(row=2, column=2, sticky="nwe")

        for w in self.winfo_children():
            w.grid(padx=4)
            w.grid(pady=2)

    def put_up_new_msg(self):
        msg, group_id, send_from = self.new_msg.get()
        if msg:                      # put up non-empty new message
            if send_from:               # send from users
                msg = f"\n[{send_from}] {msg}"
            else:                                   # send from system
                msg = '\n' + msg
            self.cache[group_id] += msg  # write to group history

            if group_id == self.cur_group_id:       # update current chat_box if user is in the chat_box of group_id
                self.chat_box.config(state=tk.NORMAL)
                self.chat_box.insert(tk.END, msg)
                self.chat_box.config(state=tk.DISABLED)
                self.chat_box.see(tk.END)

            self.new_msg.clear()                    # set new message to empty

    def switch_to(self, group_id):
        if group_id == -1:
            self.switch_to(utils.SYS_GRP_ID)
        if group_id == self.cur_group_id:
            pass
        elif group_id in self.cache:
            self.chat_box.config(state=tk.NORMAL)
            self.chat_box.delete('1.0', 'end')          # delete the content of current chat_box
            self.chat_box.insert('1.0', self.cache[group_id]) # put up history of group_id
            self.chat_box.config(state=tk.DISABLED)
            self.chat_box.see(tk.END)

            self.cur_group_id = group_id
            self.root.leave_group_btn.set_command()
        else:
            self.new_msg.set(new_content=f"[ERROR] group with id: {group_id} does not exist",
                             group_id=utils.SYS_GRP_ID)
            self.put_up_new_msg()
            self.switch_to(utils.SYS_GRP_ID)


    def leave_group(self, group_name):
        """
        leave the group permanently
        """
        if utils.VERBOSE:
            print("leave_group called once")
        if group_name in self.root.group_frame.group_list_dict:
            self.root.client.leave_group(group_name)
        else:
            raise Exception(f"{group_name} is not {self.root.client.name}'s group\nWhy, my god why?")

        pass

    def chat(self, message: str, group_id: int):
        if not message.isspace():       # won't send empty message
            # if user talk to system, echo the message
            if self.cur_group_id == utils.SYS_GRP_ID:
                self.new_msg.set(f"[{self.root.client.name}] {message.rstrip()}")
                self.put_up_new_msg()
            else:
                if utils.VERBOSE:
                    print(message, group_id)
                self.root.client.chat(message=message,
                                      group_id=group_id)



class Status_frame(tk.Frame):
    """
    This is the frame that display the status of the user.
    """
    def __init__(self, root: Main_GUI):
        super(Status_frame, self).__init__(root.chat_frame)
        self.root = root
        self._client_name = tk.StringVar()

        self._client_name.set("Username:    ")

        self._client_state_int = utils.S_OFFLINE
        self._state2str = utils.STATE2STR
        self._client_state = tk.StringVar()
        self._client_state.set(f"State: {self._state2str[self._client_state_int]}")


        self.name_lbl = tk.Label(self,
                                 textvariable=self._client_name,
                                 bg=utils.WHITE,
                                 fg=utils.BLACK,
                                 font=utils.FONT_NORMAL)
        self.name_lbl.grid(row=0, column=0, sticky="nw")

        self.state_lbl = tk.Label(self,
                                  textvariable=self._client_state,
                                  bg=utils.WHITE,
                                  fg=utils.BLACK,
                                  font=utils.FONT_NORMAL)
        self.state_lbl.grid(row=0, column=1, sticky="nw")

        #
        # self.rowconfigure(0, weight=1)
        # self.columnconfigure(0, weight=1)

        for w in self.winfo_children():
            w.grid(padx=4)
            w.grid(pady=2)


    @property
    def client_name(self):
        return self._client_name.get()

    @client_name.setter
    def client_name(self, value):
        if isinstance(value, str):
            self._client_name.set(f"Username: {value}")
        else:
            raise TypeError(f"Status_frame.name must be a str (not {type(value)}).")

    @property
    def client_state(self):
        return self._client_state_int

    @client_state.setter
    def client_state(self, value):
        if value in self._state2str:
            self._client_state.set(f"State: {self._state2str[value]}")
        else:
            raise TypeError(f"Status_frame.client_state must be an int in "
                            f"range({min(self._state2str)}, {max(self._state2str)}) "
                            f"(not {type(value)}: {value})")


if __name__ == "__main__":
    my_chatroom = Main_GUI()
    my_chatroom.app()
    my_chatroom.mainloop()


