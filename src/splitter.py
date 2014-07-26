#!/usr/bin/python -O
# -*- coding: iso-8859-15 -*-

# {{{ Imports

from __future__ import print_function
import time
import sys
import socket
import threading
import struct
import argparse
from color import Color
import common
from splitter_ims import Splitter_IMS
from splitter_dbs import Splitter_DBS

# }}}

class Splitter():

    def __init__(self):

        # {{{ Args parsing

        parser = argparse.ArgumentParser(description='This is the splitter node of a P2PSP team.')

        #parser.add_argument('--splitter_addr', help='IP address to serve (TCP) the peers. (Default = "{}")'.format(Splitter_IMS.SPLITTER_ADDR)) <- no ahora

        parser.add_argument('--buffer_size', help='size of the video buffer in blocks. Default = {}.'.format(Splitter_IMS.BUFFER_SIZE))

        parser.add_argument('--channel', help='Name of the channel served by the streaming source. Default = "{}".'.format(Splitter_IMS.CHANNEL))

        parser.add_argument('--chunk_size', help='Chunk size in bytes. Default = {}.'.format(Splitter_IMS.CHUNK_SIZE))

        parser.add_argument('--header_size', help='Size of the header of the stream in chunks. Default = {}.'.format(Splitter_IMS.HEADER_SIZE))

        parser.add_argument('--losses_memory', help='Number of chunks to divide by two the losses counters. Makes sense only in unicast mode. Default = {}.'.format(Splitter_DBS.LOSSES_MEMORY))

        parser.add_argument('--losses_threshold', help='Maximum number of lost chunks for an unsupportive peer. Makes sense only in unicast mode. Default = {}.'.format(Splitter_DBS.LOSSES_THRESHOLD))

        parser.add_argument("--mcast", action="store_true", help="Enables IP multicast.")

        parser.add_argument('--mcast_addr', help='IP multicast address used to serve the chunks. Makes sense only in multicast mode. Default = "{}".'.format(Splitter_IMS.MCAST_ADDR))

        parser.add_argument('--port', help='Port to serve the peers. Default = "{}".'.format(Splitter_IMS.PORT))

        parser.add_argument('--source_addr', help='IP address of the streaming server. Default = "{}".'.format(Splitter_IMS.SOURCE_HOST))

        parser.add_argument('--source_port', help='Port where the streaming server is listening. Default = {}.'.format(Splitter_IMS.SOURCE_PORT))

        args = parser.parse_known_args()[0]

        if args.mcast:
            splitter = Splitter_IMS()

            if args.mcast_addr:
                splitter.MCAST_ADDR = args.mcast_addr
        else:
            splitter = Splitter_DBS()

            if args.losses_memory:
                splitter.LOSSES_MEMORY = int(args.losses_memory)

            if args.losses_threshold:
                splitter.LOSSES_THRESHOLD = int(args.losses_threshold)

        if args.buffer_size:
            splitter.BUFFER_SIZE = int(args.buffer_size)

        if args.channel:
            print("---------------->", splitter.CHANNEL)
            splitter.CHANNEL = args.channel
            print("---------------->", splitter.CHANNEL)

        if args.chunk_size:
            splitter.CHUNK_SIZE = int(args.chunk_size)

        if args.header_size:
            splitter.HEADER_SIZE = int(args.header_size)

        if args.port:
            splitter.PORT = int(args.port)

        if args.source_addr:
            splitter.SOURCE_HOST = socket.gethostbyname(args.source_addr)

        if args.source_port:
            splitter.SOURCE_PORT = int(args.source_port)

        # }}}

        # {{{

        splitter.start()

        if args.mcast:
            # {{{ Prints information until keyboard interruption

            # #Chunk #peers { peer #losses period #chunks }

            #last_chunk_number = 0
            while splitter.alive:
                try:
                    sys.stdout.write(Color.white)
                    print('%5d' % splitter.chunk_number, end=' ')
                    sys.stdout.write(Color.none)
                    print('|', end=' ')
                    print()
                    time.sleep(1)

                except KeyboardInterrupt:
                    print('Keyboard interrupt detected ... Exiting!')

                    # Say to the daemon threads that the work has been finished,
                    splitter.alive = False

                    # Wake up the "handle_arrivals" daemon, which is waiting
                    # in a peer_connection_sock.accept().
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect((socket.gethostname(), splitter.PORT))
                    sock.recv(1024*10) # Header
                    sock.recv(struct.calcsize("H")) # Buffer size
                    sock.recv(struct.calcsize("H")) # Chunk size

                    # Breaks this thread and returns to the parent process
                    # (usually, the shell).
                    break

            # }}}
        else:
            # {{{ Prints information until keyboard interruption

            # #Chunk #peers { peer #losses period #chunks }

            #last_chunk_number = 0
            while splitter.alive:
                try:
                    sys.stdout.write(Color.white)
                    print('%5d' % splitter.chunk_number, end=' ')
                    sys.stdout.write(Color.cyan)
                    print(len(splitter.peer_list), end=' ')
                    for p in splitter.peer_list:
                        sys.stdout.write(Color.blue)
                        print(p, end= ' ')
                        sys.stdout.write(Color.red)
                        print('%3d' % splitter.losses[p], '<', splitter.LOSSES_THRESHOLD, end=' ')
                        try:
                            sys.stdout.write(Color.blue)
                            print('%3d' % splitter.period[p], end= ' ')
                            sys.stdout.write(Color.purple)
                            print('%4d' % splitter.number_of_sent_chunks_per_peer[p], end = ' ')
                            splitter.number_of_sent_chunks_per_peer[p] = 0
                        except AttributeError:
                            pass
                        sys.stdout.write(Color.none)
                        print('|', end=' ')
                    print()
                    '''
                    print "[%3d] " % len(splitter.peer_list),
                    kbps = (splitter.chunk_number - last_chunk_number) * \
                    splitter.CHUNK_SIZE * 8/1000
                    last_chunk_number = splitter.chunk_number

                    for x in xrange(0,kbps/10):
                    print "\b#",
                    print kbps, "kbps"
                    '''
                    time.sleep(1)

                except KeyboardInterrupt:
                    print('Keyboard interrupt detected ... Exiting!')

                    # Say to the daemon threads that the work has been finished,
                    splitter.alive = False

                    # Wake up the "moderate_the_team" daemon, which is waiting
                    # in a cluster_sock.recvfrom(...).
                    splitter.say_goodbye((splitter.TEAM_HOST, splitter.TEAM_PORT), splitter.team_socket)

                    # Wake up the "handle_arrivals" daemon, which is waiting
                    # in a peer_connection_sock.accept().
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect((splitter.TEAM_HOST, splitter.TEAM_PORT))
                    sock.recv(1024*10) # Header
                    sock.recv(struct.calcsize("H")) # Buffer size
                    sock.recv(struct.calcsize("H")) # Chunk size
                    number_of_peers = socket.ntohs(struct.unpack("H", sock.recv(struct.calcsize("H")))[0])
                    # Receive the list
                    while number_of_peers > 0:
                        sock.recv(struct.calcsize("4sH"))
                        number_of_peers -= 1

                    # Breaks this thread and returns to the parent process
                    # (usually, the shell).
                    break

            # }}}

        # }}}

x = Splitter()
