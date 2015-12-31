
import SocketServer
import logging
import threading
import os
import socket
import sys
from ulities.strings import handle_message_request, disconnect_request_string, join_chat_room, leave_chat_room_request





studentNumber = "8225096d25e2f49ea3efabe515fd9f58707934a0cb3a9494aea8d64ec363cd17"
joinRoomString = "JOIN_CHATROOM"
leaveRoomString = "LEAVE_CHATROOM"
sendMessageString = "CHAT"
disconnectString= "DISCONNECT"

if os.name != "nt":
    import fcntl
    import struct

    def get_interface_ip(ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s',
                                ifname[:15]))[20:24])

def get_lan_ip():
    ip = socket.gethostbyname(socket.gethostname())
    if ip.startswith("127.") and os.name != "nt":
        interfaces = [
            "eth0",
            "eth1",
            "eth2",
            "wlan0",
            "wlan1",
            "wifi0",
            "ath0",
            "ath1",
            "ppp0",
            ]
        for ifname in interfaces:
            try:
                ip = get_interface_ip(ifname)
                break
            except IOError:
                pass
    return ip


class ThreadedTCPHandler(SocketServer.BaseRequestHandler):

    def setup(self):
        self.client_connected=True
        self.return_string= ""
        self.join_id= -1
        self.room_refs= []

    def handle(self):
        while(self.client_connected):

            request_string = self.request.recv(1024)
            request_exists = (not request_string == "")

            if ("KILL_SERVICE" in request_string):
                #print ("Service killed by Client\n")
                self.client_connected=False
                chat_server.server_alive = False

            elif ("HELO" in request_string):
                #print(request_string)
                lines=request_string.split()
                request_string = ("HELO {}\nIP:{}\nPort:{}\nStudentID:{}\n".format(lines[1], my_ip, p, studentNumber))
                self.request.send(request_string)

            elif(joinRoomString in request_string):
                logging.info("\nJOIN REQUEST:")
                self.join_id, self.new_room_ref =handleJoin(request_string, self.request)
                #print(self.join_id)
                self.room_refs.append(self.new_room_ref)

            elif(leaveRoomString in request_string):
                logging.info("\nLEAVE REQUEST:")
                self.left_room=handleLeave(request_string)
                try:
                    self.room_refs.remove(self.left_room)
                except:
                    pass

            elif(disconnectString in request_string):
                logging.info("DISCONNECT: Client_ID: {} has disconnected.".format(self.join_id))
                handleDisconnect(request_string)
                print("Disconnecting")
                self.client_connected=False

            elif(sendMessageString in request_string):
                handle_message(request_string)
            elif( request_exists== False):
                pass
            else:
                logging.warning("Client Request: Invalid command syntax")


def handleJoin(request_string, request):
    join_room_name,client_ip,client_port,client_name= join_chat_room(request_string)
    room_exists=chat_server.room_exists(join_room_name)
    client_exists=chat_server.client_exists(client_name)
    logging.info("Client exists: {} - Room exists: {}".format(client_exists,room_exists))

    if not client_exists:
        chat_server.add_client_to_server(client_ip,client_port,client_name, request)
        logging.info("{} added to the server".format(client_name))
    else:

        logging.info("{} already exists on the server".format(client_name))

    client=chat_server.get_client(client_name)
    chat_server.clients[client.join_id].req=request
    if not room_exists:
        #adding room to the server
        chat_server.add_room_to_server(join_room_name)
        room_ref=chat_server.get_room_ref(join_room_name)
        #adding client to the newly created room
        chat_server.clients[client.join_id].success_join_message(join_room_name, room_ref)
        chat_server.chat_rooms[room_ref].join(client.join_id,client_name)
        logging.info("{} created and {} added".format(join_room_name, client_name))
        return client.join_id, room_ref
    else:
        #room exists
        room=chat_server.get_room(join_room_name)
        chat_server.clients[client.join_id].success_join_message(join_room_name, room.ref)
        #make sure the client is not already a member
        if(not client.join_id in room.member_IDs):
            #add client to room
            room.join(client.join_id, client_name)
            chat_server.clients[client.join_id].set(client)
            logging.info("{} added to {}".format(client_name, join_room_name))


        return client.join_id, room.ref

def handleLeave(request_string):
    room_ref,join_id,client_name=leave_chat_room_request(request_string)
    room_exists=chat_server.room_exists(chat_server.chat_rooms[room_ref].name)
    logging.info("Room exists: {}".format(room_exists))
    if not room_exists:
         "ERROR_CODE: 3\nERROR_DESCRIPTION: Can not leave. Chat room does not exist"
    else:
        client=chat_server.clients[join_id]
        client.success_left_message(room_ref)
        room=chat_server.chat_rooms[room_ref]
        room.leave(join_id,client_name)
        logging.info("{} left".format(client_name))
        return room_ref

def handleDisconnect(request_string):
    disconnect_string,port,client_name=disconnect_request_string(request_string)
    client=chat_server.get_client(client_name)
    #client.add_message("FUck yall im out")
    for room in chat_server.chat_rooms:
        if(client.join_id in room.member_IDs):
            room.leave(client.join_id,client_name)
    #chat_server.clients[client.join_id]= None


def handle_message(request_string):
    logging.info("/n MESSAGE PROCESSING")
    room_ref,join_id,client_name,message= handle_message_request(request_string)
    chat_server.chat_rooms[room_ref].normal_message( client_name, join_id, message)

class client:

    def __init__(self, ip, port, name, request):
        self.ip = ip
        self.port = port
        self.name = name
        self.messages= []
        self.req=request
        self.test=0
        self.join_id = chat_server.number_of_clients

        #print(chat_server.number_of_clients, "num clients")
        chat_server.number_of_clients+= 1

    def add_message(self, message):

        self.test+=1
        #print("New message for {},ID:{}:\n{}\nThis is the {} call".format(self.name,self.join_id, message,self.test))
        self.req.send(message)

       # if self.test==8 and self.join_id==1:
       #         print("sending that shit{}".format(self.test))
       #         self.req.send("CHAT:0\nCLIENT_NAME:client1\nMESSAGE:hello world from client 1\n\n")
       #         self.req.send("CHAT:0\nCLIENT_NAME:client2\nMESSAGE:hello world from client 2\n\n")
       # elif self.test==9 and self.join_id==1:
       #     print("sending that shit{}".format(self.test))
       #     self.req.send("CHAT:0\nCLIENT_NAME:client1\nMESSAGE:hello world from client 1\n\n")
       # else:
       #     print("made it {} for {}".format(self.test,self.join_id))
        #    self.req.send(message)
       # self.messages.append(message)

        #for x in self.messages:
        #    if self.join_id==1:
        #            logging.info("Printing past:"+x)

    def clear_messages(self):
        self.messages=[]

    def get_messages(self):
        return self.messages

    def messages_exist(self):
        if self.messages:
            return True
        else:
            return False

    def success_join_message(self, chatroom_name, room_ref):
        serverIP, serverPort = chat_server.server_address
        JOINED_CHATROOM = "JOINED_CHATROOM:{}\n".format(chatroom_name)
        SERVER_IP = "SERVER_IP:{}\n".format(serverIP)
        PORT = "PORT:{}\n".format(serverPort)
        ROOM_REF = "ROOM_REF:{}\n".format(room_ref)
        JOIN_ID = "JOIN_ID:{}\n".format(self.join_id)
        logging.info("Join Message Parsed for {}".format(self.name))
        #print(JOINED_CHATROOM+SERVER_IP+PORT+ROOM_REF+JOIN_ID)
        self.add_message(JOINED_CHATROOM+SERVER_IP+PORT+ROOM_REF+JOIN_ID)

    def success_left_message(self, room_ref):
        self.add_message("LEFT_CHATROOM:{}\nJOIN_ID:{}\n".format(room_ref,self.join_id))

    def get(self):
        return self

    def set(self, updated_client):
        self=updated_client

class chat_room():

    def __init__(self, room_name):
        self.name= room_name
        self.ref=chat_server.number_of_rooms
        self.member_IDs = []
        chat_server.number_of_rooms+=1
        self.lock=threading._RLock()
        logging.info("{} created".format(room_name))

    def new_message(self, sender_name, sender_id, message):
        #self.lock.acquire()
        #
        print("New_message:\n{}".format(message))
        #if(self.authenticate(sender_id)):
        if(True):
            cleaned=message.replace('\n','')
            for recpiant_ID in self.member_IDs:
                recpiant = chat_server.clients[recpiant_ID].get()
                formated= "CHAT:{}\nCLIENT_NAME:{}\nMESSAGE:{}\n\n".format(self.ref, sender_name, cleaned)
                recpiant.add_message(formated)
                chat_server.clients[recpiant_ID].set(recpiant)
        else:
            "ERROR_CODE: 10 \nERROR_DESCRIPTION: You are not a member of this chat"

    def normal_message(self, sender_name, sender_id, message):
        self.lock.acquire()
        if(sender_id in self.member_IDs):
            self.new_message(sender_name, sender_id, message)
        else:
            print("incorrect Id")
            chat_server.get_client(sender_name).add_message("ERROR_CODE: 5\nERROR_DESCRIPTION: Incorrect ID and Name")
        self.lock.release()

    def authenticate(self, sender_id):
        return ((sender_id in self.member_IDs) or (sender_id=="leaving_message"))

    def join(self, join_id, client_name):
        #print("Made it into join")
        self.lock.acquire()
        #print("{} accquired the lock{}".format(client_name,self.lock._is_owned()))
        logging.info("Joining: {}".format(client_name))
        self.member_IDs.append(join_id)
        self.chatroom_join_message(client_name,join_id)
        #print("{} realeased {} ".format(client_name,self.lock._is_owned()))
        self.lock.release()
        #print("{} actually realeased ".format(client_name))
        #self.new_message(client_name, join_id, "{} joined {}".format(client_name,self.name))

    def leave(self, join_id, client_name):
       # try:
        self.lock.acquire()
        self.chatroom_leave_message(client_name, join_id)
        self.member_IDs.remove(join_id)
        self.lock.release()
       # except UnboundLocalError:
        #    logging.warning("{} is not in that group".format(join_id))

    def chatroom_join_message(self,client_name, join_id):

        #print("chat_join_message")
        self.new_message(client_name, join_id, "{} has joined this chatroom.".format(client_name))

    def chatroom_leave_message(self,client_name, join_id):
        #print("chat_leave_message")
        self.new_message(client_name, join_id, "{} has left this chatroom.".format(client_name))

    def get(self):
        return self

    def set(self, updated_room):
        self = updated_room

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):

    def add_client_to_server(self, ip, port, name, request):
        self.new_client= client(ip, port, name, request)
        self.clients.append(self.new_client)

    def add_room_to_server(self, room_name):
        self.new_room = chat_room(room_name)
        self.chat_rooms.append(self.new_room)

    def client_exists(self, client_name):
        for existing_client in self.clients:
            if existing_client.name==client_name:
                return True
        return False

    def room_exists(self, room_name):
        for existing_room in self.chat_rooms:
            if existing_room.name==room_name:
                return True
        return False

    def get_clients(self):
        return self.clients

    def set_clients(self, updated_clients):
        self.clients=updated_clients

    def get_client(self, client_name):
        for client in self.clients:
            if client.name==client_name:
                return client
        return -1

    def get_room_ref(self, room_name):
        for room in self.chat_rooms:
            if room.name==room_name:
                return room.ref
        return -1

    def get_room(self, room_name):
        for existing_room in self.chat_rooms:
            if existing_room.name==room_name:
                return existing_room
        return -1

    def get_room_by_ref(self, room_ref):
        for existing_room in self.chat_rooms:
            if existing_room.ref==room_ref:
                return existing_room
        return -1


if __name__ == "__main__":
    logging.basicConfig(filename='logging.log',level=logging.DEBUG)
    my_ip = get_lan_ip()
    h, p = my_ip, int(sys.argv[1])
    chat_server = ThreadedTCPServer((h, p), ThreadedTCPHandler)
    serverIP, serverPort = chat_server.server_address  # find out what port we were given

    chat_server.request_queue_size = 10
    chat_server.server_alive = True
    chat_server.clients = []
    chat_server.chat_rooms = []
    chat_server.number_of_rooms = 0
    chat_server.number_of_clients = 0

    print(serverIP)
    print(serverPort)


    try:
        server_thread = threading.Thread(target=chat_server.serve_forever)
        server_thread.daemon = True
        server_thread.start()

        while(chat_server.server_alive==True):
            pass

        chat_server.shutdown()
        chat_server.server_close()
        exit()

    except KeyboardInterrupt:
        print("Key board interrupt \nServer Shutting Down")
        chat_server.shutdown()
        chat_server.server_close()
        exit()