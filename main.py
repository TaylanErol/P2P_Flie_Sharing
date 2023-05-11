import math
import threading
import os
import time
import json
import socket

CHUNK_SIZE = 1024  # Size of a chunk in bytes
CHUNK_NUM = 5  # Number of chunks per file
ANNOUNCE_PERIOD = 60  # Time between announcements in seconds
broadcast_address = '192.168.43.1'

def file_splitter(content_name):
    # content_name = 'py'  # This'll be the parameter you provide for this code. The name of the content that the user wants to download.
    filename = content_name+'.png'
    c = os.path.getsize(filename)
    print('file size is: ' , c , '\n')
    CHUNK_SIZE = math.ceil(math.ceil(c)/5)
    print('chunk count is 5 and chunk size is: ',CHUNK_SIZE, '\n')

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


def run_and_announce_chunks(directory):
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((socket.gethostname(), 5001))

    # Ask the user for the initial file
    content_name = input("Enter the name of the file to host (without extension): ")
    file_splitter(content_name)

    # Start announcing chunks
    while True:
        # Read the names of the chunk files
        chunk_files = [f for f in os.listdir(directory) if f.startswith(content_name + "_")]

        # Create the announcement message
        message = json.dumps({"chunks": chunk_files}).encode('utf-8')

        sock.sendto(message, (broadcast_address, 5001))

        time.sleep(ANNOUNCE_PERIOD)


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')
    directory = input('Enter directory... \n')
    run_and_announce_chunks(directory)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
