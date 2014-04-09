#!/usr/bin/python
import sys
import SimpleXMLRPCServer
import md5

hashes = []
pows = []
peers = set()
pid = 0

def mkhash(s):
    return md5.new(s).hexdigest()

def init_pid():
    global pid
    pid = 0
    if len(sys.argv) > 1:
        pid = int(sys.argv[1])

def init_hashes():
    global hashes
    fo = open("Dosref", "r")
    for x in range(0, 5 * pid):
        fo.readline()
    for x in range(0, 5):
        passwd = ((fo.readline()).strip())[-3:]
        hashes.append(mkhash(passwd))
    fo.close();

def init_peers():
    global pid
    global peers
    fo = open("Topologia", "r")
    for line in fo:
        a, b = line.split()
        a = int(a)
        b = int(b)
        if a == pid:
            url = "http://localhost:" + str(8000 + b)
            peers.add(url)
    fo.close();

#hashes = [ mkhash("aB"), mkhash("b") ]
#    def kill(self):
        

#server = SimpleXMLRPCServer.SimpleXMLRPCServer(("localhost", 8000))
#server.register_instance(Functions())
#server.serve_forever()

#print "opa"

#print 'Number of arguments:', len(sys.argv), 'arguments.'
#print 'Argument List:', str(sys.argv)

class StoppableRPCServer(SimpleXMLRPCServer.SimpleXMLRPCServer):

    stopped = False
    allow_reuse_address = True

    def __init__(self, *args, **kw):
        SimpleXMLRPCServer.SimpleXMLRPCServer.__init__(self, *args, **kw)
        self.register_function(lambda: 'OK', 'ping')

    def serve_forever(self):
        while not self.stopped:
            self.handle_request()

    def force_stop(self):
        self.server_close()
        self.stopped = True
        self.create_dummy_request()

    def create_dummy_request(self):
        server = xmlrpclib.Server('http://%s:%s' % self.server_address)
        server.ping()

init_pid()
init_hashes()
init_peers()

server = StoppableRPCServer(("localhost", 8000))

class Functions:
    def getPeers(self, list):
        for x in list:
            peers.add(x)
        return list(peers)
        
    def getHashes(self):
        return hashes
    def sendPasswords(self, res):
        print "Found: ", res
        return False
    def matar(self):
        global server
        server.force_stop()
        return False

server.register_instance(Functions())
server.serve_forever()

print hashes
print list(peers)
