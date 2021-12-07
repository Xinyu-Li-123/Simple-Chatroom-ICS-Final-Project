import socket
import time
import tkinter as tk
# use local loop back address by default
#CHAT_IP = '127.0.0.1'
# CHAT_IP = socket.gethostby[SYSTEM]\t(socket.gethostname())
# @c CHAT_IP = ''#socket.gethostbyname(socket.gethostname())
CHAT_IP = "localhost"    # @d

CHAT_PORT = 6000
SERVER = (CHAT_IP, CHAT_PORT)

S_OFFLINE   = 0
S_CONNECTED = 1
S_LOGGEDIN  = 2
S_CHATTING  = 3

VERBOSE = True

NEED_INIT = False

STATE2STR = {0: "Offline",
             1: "Connected",
             2: "Logged In",
             3: "Chatting"}     # the values are shown to the user in GUI
SIZE_SPEC = 5

CHAT_WAIT = 0.2

MAX_GROUP_NUM = 10
MAX_HISTORY_MSG = 5

WHITE = "#ffffff"
LIGHTGREY = "#b4cac7"
GREY = "#708482"
DEEPGREY = "#4f6261"
BLACK = "#17252a"

FONT_NORMAL = ["Comic Sans MS", 10]
FONT_LARGE = ["Comic Sans MS", 12]

DB_NAME="ICS_Chatroom_Database"
# DB_NAME="test_database"
DB_PATH = "./database/{db_name}.db".format(db_name=DB_NAME)
SYS_GRP_ID = 200000

def print_state(state):
    print('**** State *****::::: ')
    if state == S_OFFLINE:
        print('Offline')
    elif state == S_CONNECTED:
        print('Connected')
    elif state == S_LOGGEDIN:
        print('Logged in')
    elif state == S_CHATTING:
        print('Chatting')
    else:
        print('Error: wrong state')

def mysend(s, msg):
    #append size to message and send it
    msg = ('0' * SIZE_SPEC + str(len(msg)))[-SIZE_SPEC:] + str(msg)
    msg = msg.encode()
    total_sent = 0
    while total_sent < len(msg) :
        sent = s.send(msg[total_sent:])
        if sent==0:
            print('server disconnected')
            break
        total_sent += sent

def myrecv(s):
    #receive size first
    size = ''
    while len(size) < SIZE_SPEC:
        text = s.recv(SIZE_SPEC - len(size)).decode()
        if not text:
            # print('disconnected')
            return ''
        size += text
    size = int(size)
    #now receive message
    msg = ''
    while len(msg) < size:
        text = s.recv(size-len(msg)).decode()
        if text == b'':
            print('disconnected')
            break
        msg += text
    #print ('received '+message)

    return msg

def text_proc(text, user):
    ctime = time.strftime('%d.%m.%y,%H:%M', time.localtime())
    return('(' + ctime + ') ' + user + ' : ' + text) # message goes directly to screen
