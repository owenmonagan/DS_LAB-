import logging


def handle_message_request(request_string):
    logging.info("Message string processing")
    lines= request_string.split()
    room_ref = int(lines[1])
    join_id = int(lines[3])
    client_name = lines[5]
    message = request_string.split("MESSAGE:")[1]
    logging.info('Values processed:{}, {}, {}, {}'.format(room_ref,join_id,client_name,message))
    return room_ref,join_id,client_name,message

def disconnect_request_string(request_string):
    logging.info("\nDISCONNECTING: string processing")
    lines= request_string.split()
    disconnect_string = lines[0].split(":")[1]
    port = lines[1].split(":")[1]
    client_name = lines[2].split(":")[1]
    logging.info('LEAVING: Values processed:{}, {}, {}'.format(disconnect_string,port,client_name))
    return disconnect_string,port,client_name

def join_chat_room(join_string):
    logging.info("Join chat room string processing")
    lines= join_string.split()
    join_room = lines[0].split(":")[1]
    client_ip = lines[1].split(":")[1]
    client_port = lines[2].split(":")[1]
    client_name = lines[3].split(":")[1]
    logging.info('Values processed:{}, {}, {}, {}'.format(join_room,client_ip,client_port,client_name))
    return join_room,client_ip,client_port,client_name

    
def leave_chat_room_request(leave_string):
    logging.info("\nLEAVING: string processing")
    lines= leave_string.split()
    room_ref = int(lines[1])
    join_id = int(lines[3])
    client_name = lines[5].rstrip("\n")
    logging.info('LEAVING: Values processed:{}, {}, {}'.format(room_ref,join_id,client_name))
    return room_ref,join_id,client_name