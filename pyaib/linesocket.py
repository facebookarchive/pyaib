#!/usr/bin/env python
#
# Copyright 2013 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
"""
Line based socket using gevent
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import errno

import gevent
from gevent import socket
from gevent import queue, select
from OpenSSL import SSL

from .util.decorator import utf8Encode, utf8Decode, raise_exceptions


class LineSocketBuffers(object):
    def __init__(self):
        self.readbuffer = bytearray()
        self.writebuffer = bytearray()

    def clear(self):
        del self.readbuffer[0:]
        del self.writebuffer[0:]

    def readbuffer_mv(self):
        return memoryview(self.readbuffer)

    def writebuffer_mv(self):
        return memoryview(self.writebuffer)

#We use this to end lines we send to the server its in the RFC
#Buffers don't support unicode just yet so 'encode'
LINEENDING = b'\r\n'


class LineSocket(object):
    """Line based socket impl takes a host and port"""
    def __init__(self, host, port, SSL):
        self.host, self.port, self.SSL = (host, port, SSL)
        self._socket = None
        self._buffer = LineSocketBuffers()
        #Thread Safe Queues for
        self._IN = queue.Queue()
        self._OUT = queue.Queue()

    #Exceptions for LineSockets
    class SocketError(Exception):
        def __init__(self, value):
            self.value = value

        def __str__(self):
            return repr(self.value)

    # Connect to remote host
    def connect(self):
        host, port = (self.host, self.port)

        #Clean out the buffers
        self._buffer.clear()

        #If the existing socket is not None close it
        if self._socket is not None:
            self.close()

        # Resolve the hostname and connect (ipv6 ready)
        sock = None
        try:
            for info in socket.getaddrinfo(host, port, socket.AF_UNSPEC,
                                           socket.SOCK_STREAM):
                family, socktype, proto, canonname, sockaddr = info

                #Validate the socket will make
                try:
                    sock = socket.socket(family, socktype, proto)

                    #Set Keepalives
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                except socket.error as msg:
                    print('Socket Error: %s' % msg)
                    sock = None
                    continue

                #Wrap in ssl if asked
                if self.SSL:
                    print('Starting SSL')
                    try:
                        ctx = SSL.Context(SSL.SSLv23_METHOD)
                        sock = SSL.Connection(ctx, sock)
                    except SSL.Error as err:
                        print('Could not Initiate SSL: %s' % err)
                        sock = None
                        continue

                #Try to establish the connection
                try:
                    print('Trying Connect(%s)' % repr(sockaddr))
                    sock.settimeout(10)
                    sock.connect(sockaddr)
                except socket.error as msg:
                    print('Socket Error: %s' % msg)
                    if self.SSL:
                        try:
                            sock.shutdown()
                        except SSL.Error as e:
                            print('Failed to shutdown SSL: %s' % e)
                    sock.close()
                    sock = None
                    continue
                break
        except Exception as e:
            print('Some unknown exception: %s' % e)

        #After all the connection attempts and sock is still none lets bomb out
        if sock is None:
            print('Could not open connection')
            return False

        #Set the socket to non_blocking
        sock.setblocking(0)

        print("Connection Open.")
        self._socket = sock
        return True

    #Start up the read and write threads
    def run(self):
        #Fire off some greenlits to handing reading and writing
        try:
            print("Starting Read/Write Loops")
            tasks = [gevent.spawn(raise_exceptions(self._read)),
                     gevent.spawn(raise_exceptions(self._write))]
            #Wait for a socket exception and raise the flag
            select.select([], [], [self._socket])  # Yield
            raise self.SocketError('Socket Exception')
        finally:  # Make sure we kill the tasks
            print("Killing read and write loops")
            gevent.killall(tasks)

    def close(self):
        if self.SSL:
            try:
                self._socket.shutdown()
            except:
                pass
        self._socket.close()
        self._socket = None

    #Read from the socket, split out lines into a queue for readline
    def _read(self):
        eof = False
        while True:
            try:
                #Wait for when the socket is ready for read
                select.select([self._socket], [], [])  # Yield
                data = self._socket.recv(4096)
                if not data:  # Disconnected Remote
                    eof = True
                self._buffer.readbuffer.extend(data)
            except SSL.WantReadError:
                pass  # Nonblocking ssl yo
            except (SSL.ZeroReturnError, SSL.SysCallError):
                eof = True
            except socket.error as e:
                if e.errno == errno.EAGAIN:
                    pass  # Don't Care
                else:
                    raise

            #If there are lines to proccess do so
            while LINEENDING in self._buffer.readbuffer:
                #Find the buffer offset
                size = self._buffer.readbuffer.find(LINEENDING)
                #Get the string from the buffer
                line = self._buffer.readbuffer_mv()[0:size].tobytes()
                #Place the string the the queue for safe handling
                #Also convert it to unicode
                self._IN.put(line)
                #Delete the line from the buffer + 2 for line endings
                del self._buffer.readbuffer[0:size + 2]

            # Make sure we parse our readbuffer before we return
            if eof:  # You would think reading from a disconnected socket would
                     # raise an excaption
                raise self.SocketError('EOF')

    #Read Operation (Block)
    @utf8Decode.returnValue
    def readline(self):
        return self._IN.get()

    #Write Operation
    def _write(self):
        while True:
            line = self._OUT.get()  # Yield Operation
            self._buffer.writebuffer.extend(line + LINEENDING)

            #If we have buffers to write lets write them all
            while self._buffer.writebuffer:
                try:
                    gevent.sleep(0)  # This gets tight sometimes
                    #Try to dump 4096 bytes to the socket
                    count = self._socket.send(
                        self._buffer.writebuffer_mv()[0:4096])
                    #Remove sent len from buffer
                    del self._buffer.writebuffer[0:count]
                except SSL.WantReadError:
                    gevent.sleep(0)  # Yield so this is not tight
                except socket.error as e:
                    if e.errno == errno.EPIPE:
                        raise self.SocketError('Broken Pipe')
                    else:
                        raise self.SocketError('Err Socket Code: ' + e.errno)
                except SSL.SysCallError as e:
                    (errnum, errstr) = e
                    if errnum == errno.EPIPE:
                        raise self.SocketError(errstr)
                    else:
                        raise self.SocketError('SSL Syscall (%d) Error: %s'
                                               % (errnum, errstr))

    #writeline Operation [Blocking]
    @utf8Encode
    def writeline(self, data):
        self._OUT.put(data)
