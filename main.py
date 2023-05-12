import math
import threading
import os
import time
import json
import socket

CHUNK_SIZE = 1024  # Size of a chunk in bytes
CHUNK_NUM = 5  # Number of chunks per file
ANNOUNCE_PERIOD = 60  # Time between announcements in seconds
broadcast_address = '192.168.1.255'

def file_splitter(content_name):
    # content_name = 'py'  # This'll be the parameter you provide for this code. The name of the content that the user wants to download.
    filename = content_name+'.png'
    c = os.path.getsize(filename)
    print('file size in bytes is: ' , c , '\n')
    CHUNK_SIZE = math.ceil(math.ceil(c)/5)
    print('chunk count is 5 and chunk size in bytes is: ',CHUNK_SIZE, '\n')

    index = 1
    with open(filename, 'rb') as infile:
        chunk = infile.read(int(CHUNK_SIZE))
        while chunk:
            chunkname = content_name+'_'+str(index)
            print("chunk name is: " + chunkname + "\n")
            with open(chunkname,'wb+') as chunk_file:
                chunk_file.write(chunk)
            index += 1
            chunk = infile.read(int(CHUNK_SIZE))
    chunk_file.close()

# def split_file_into_chunks(filename, directory):
#     with open(filename, 'rb') as file:
#         for i in range(CHUNK_NUM):
#             chunk = file.read(CHUNK_SIZE)
#             with open(f'{directory}/{filename}.chunk{i}', 'wb') as chunk_file:
#                 chunk_file.write(chunk)
#     print(f"File split into {self.CHUNK_NUM} chunks, starting to announce...")


def chunk_announcer():
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((socket.gethostname(), 5001))

    # Ask the user for the initial file
    content_name = input("Enter the name of the file to host (without extension): ")
    file_splitter(content_name)

    # Start announcing chunks
    while True:

        # Read the names of the chunk files
        chunk_files = []
        for f in os.listdir():
            if f.startswith(content_name + "_"):
                chunk_files.append(f)

        # Create the announcement message
        message = json.dumps({"chunks": chunk_files}).encode('utf-8')

        sock.sendto(message, (broadcast_address, 5001))
        print(f'Broadcasting complete waiting for {ANNOUNCE_PERIOD} seconds...')
        time.sleep(ANNOUNCE_PERIOD)

def content_discovery():
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Bind the socket to the port
    sock.bind(('0.0.0.0', 5001))

    # Initialize the content dictionary
    content_dict = {}

    while True:
        # Receive a message
        data, addr = sock.recvfrom(CHUNK_SIZE)
        print('Message recieved saving...')

        # Parse the message
        message = json.loads(data.decode('utf-8'))

        # Update the content dictionary
        for chunk in message['chunks']:
            if chunk not in content_dict:
                content_dict[chunk] = [addr[0]]
            else:
                if addr[0] not in content_dict[chunk]:
                    content_dict[chunk].append(addr[0])

        # Print the detected user and their hosted content
        print(f'{addr[0]} : {", ".join(message["chunks"])}')

        # Store the content dictionary to a file
        with open('content_dict.txt', 'w') as file:
            file.write(json.dumps(content_dict))


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')
    chunk_announcer_thread = threading.Thread(target=chunk_announcer())
    chunk_announcer_thread.start()

    # Running Content Discovery
    content_discovery_thread = threading.Thread(target=content_discovery())
    content_discovery_thread.start()

    # ... you can add other threads here ...

    # Wait for all threads to complete
    chunk_announcer_thread.join()
    content_discovery_thread.join()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
