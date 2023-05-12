import math
import threading
import os
import time
import json
import socket

CHUNK_NUM = 5  # Number of chunks per file
ANNOUNCE_PERIOD = 60  # Time between announcements in seconds
broadcast_address = '192.168.0.255'


def file_splitter(content_name):
    filename = content_name + '.png'
    c = os.path.getsize(filename)
    print('file size in bytes is: ', c, '\n')
    chunk_size = math.ceil(math.ceil(c) / CHUNK_NUM)
    print('chunk count is 5 and chunk size in bytes is: ', chunk_size, '\n')

    index = 1
    with open(filename, 'rb') as infile:
        chunk = infile.read(int(chunk_size))
        while chunk:
            chunkname = content_name + '_' + str(index)
            print("chunk name is: " + chunkname + "\n")
            with open(chunkname, 'wb+') as chunk_file:
                chunk_file.write(chunk)
            index += 1
            chunk = infile.read(int(chunk_size))
    chunk_file.close()


def chunk_announcer(content_name):
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((socket.gethostname(), 5001))

    # Ask the user for the initial file
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
        # print(f'Broadcasting complete waiting for {ANNOUNCE_PERIOD} seconds...')
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
        data, addr = sock.recvfrom(1024)
        # Parse the message
        message = json.loads(data.decode('utf-8'))

        # Update the content dictionary
        for chunk in message['chunks']:
            if chunk not in content_dict:
                content_dict[chunk] = [addr[0]]
            else:
                if addr[0] not in content_dict[chunk]:
                    # Note addr[0] is the ip adress addr[1] is port ;)
                    content_dict[chunk].append(addr[0])

        # Print the detected user and their hosted content
        print(f'{addr[0]} : {", ".join(message["chunks"])}')

        # Store the content dictionary to a file
        with open('content_dict.txt', 'w') as file:
            file.write(json.dumps(content_dict))


def chunk_downloader(content_name):
    # content_name = input('Enter the file that you want to download: \n')

    with open('content_dict.txt') as file:
        content_dict = json.loads(file.read())

    chunk_names = []
    # Go through each chunk
    for i in range(1, 6):
        chunk_name = f"{content_name}_{i}"
        chunk_names.append(chunk_name)

        # If the chunk is not in the content dictionary, print a warning and continue to the next chunk
        if chunk_name not in content_dict:
            print(f"NO KNOWN ONLINE PEER THAT ANNOUNCED {chunk_name}, CANNOT MERGE {content_name} ABORTING...")
            return

        # Try downloading the chunk from each peer until it is successfully downloaded
        for ip in content_dict[chunk_name]:
            try:
                # Establish a TCP connection and request a chunk from a peer
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((ip, 5000))  # Connect to the peer
                request = json.dumps({"requested_content": chunk_name}).encode('utf-8')
                sock.send(request)  # Send the request

                # Receive the chunk
                chunk_data = sock.recv(1024)

                # Save the chunk to a file, To remember: 'wb' is for Write Binary
                with open(chunk_name, 'wb') as chunk_file:
                    chunk_file.write(chunk_data)

                # Close the connection
                sock.close()

                # Log the download, To remember: 'a' is for Append
                with open('Download_log.txt', 'a') as log_file:
                    log_file.write(f"{time.ctime()} - {chunk_name} downloaded from {ip}\n")

                # Break the loop as the chunk has been successfully downloaded
                break
            except Exception as e:
                print(f"Failed to download {chunk_name} from {ip}: {e}, ABORTING...")
                return

    with open(content_name + '.png', 'wb') as outfile:
        for chunk in chunk_names:
            with open(chunk, 'rb') as infile:
                outfile.write(infile.read())
            infile.close()


def chunk_uploader():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # For the server to listen on all available IP addresses, use ''
    server_socket.bind(('', 5000))
    server_socket.listen()

    while True:
        # Accept a new client connection
        conn, addr = server_socket.accept()
        requested_chunk_name = 'Unknown chunk'

        try:
            # Receive the JSON request
            request = json.loads(conn.recv(1024).decode('utf-8'))
            # Get the chunk name from the request
            requested_chunk_name = request["requested_content"]

            # Open the requested chunk file and send it back to the client
            with open(requested_chunk_name, 'rb') as chunk_file:
                chunk_data = chunk_file.read()
                conn.send(chunk_data)

            # Log the file info after sending the chunk
            with open('upload_log.txt', 'a') as log_file:
                log_file.write(f"{time.ctime()} - {requested_chunk_name} sent to {addr[0]}\n")
        except Exception as e:
            print(f"Failed to send {requested_chunk_name} to {addr[0]}: {e}")
        finally:
            # Close the connection
            conn.close()


def console_sniffer():
    print("Usable commands: \n d=<requested_file_name> / downloads requested file.")
    while True:
        command = input()

        if command.startswith("d="):
            file_name = command.split('=')[1]
            # Start a new thread to download the file
            download_thread = threading.Thread(target=chunk_downloader, args=(file_name,))
            download_thread.start()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    content_name = input("Enter the name of the file to host (without extension): \n")

    # Running Chunk Announcer
    chunk_announcer_thread = threading.Thread(target=chunk_announcer, args=(content_name,))
    chunk_announcer_thread.start()

    # Running Content Discovery
    content_discovery_thread = threading.Thread(target=content_discovery)
    content_discovery_thread.start()

    # Running Chunk Uploader
    chunk_uploader_thread = threading.Thread(target=chunk_uploader)
    chunk_uploader_thread.start()

    console_sniffer_thread = threading.Thread(target=console_sniffer)
    time.sleep(2)
    console_sniffer_thread.start()

    # ... you can add other threads here ...

    # Wait for all threads to complete
    chunk_announcer_thread.join()
    content_discovery_thread.join()
    chunk_uploader_thread.join()
    console_sniffer_thread.join()
