#!/usr/bin/python
import xmlrpclib
import md5
import SimpleXMLRPCServer
import thread
import threading
import sys
import string
import time
import copy
import itertools

stopFlag = False
node_id = 0
hashes = []
pows = []
known_pows = set()
peers = set()
bctodo = []
bcdone = []
tobreak = []
broken = set()
broken_to_tell = set()
peerslock = thread.allocate_lock()

def mkhash(s):
    return md5.new(s).hexdigest()

def init_id():
    global node_id
    node_id = 0
    if len(sys.argv) > 1:
        node_id = int(sys.argv[1])

def init_hashes():
    global node_id
    global hashes
    fo = open("Dosref", "r")
    for x in range(0, 5 * node_id):
        fo.readline()
    for x in range(0, 5):
        passwd = ((fo.readline()).strip())[-3:]
        hashes.append(mkhash(passwd))
    fo.close();

def init_peers():
    global node_id
    global peers
    fo = open("Topologia", "r")
    for line in fo:
        a, b = line.split()
        a = int(a)
        b = int(b)
        if a == node_id:
            url = "http://localhost:" + str(8000 + b)
            peers.add(url)
    fo.close();

def broadcast_pow(powk):
    bctodo.add(powk)

class Functions:
    def getPeers(self, otherpeers):
        #print 'got call'
        global peers
        peerslock.acquire()
        np = copy.copy(peers)
        for x in otherpeers:
            peers.add(x)
        peerslock.release()
        return list(np)

    def getHashes(self):
        #print "6666666666666666666666bHASH"
        global hashes
        return hashes

    def sendPasswords(self, tup, p, h):
        global known_pows
        thispow = (p, h)
        pw = tup[0]
        ph = tup[1]
        if ph not in hashes:
            print "sendPasswords: not my hash"
            return 0
        if mkhash(pw) != ph:
            print "sendPasswords: incorrect hash"
            return 0
        if thispow in known_pows:
            print "sendPasswords: POW", thispow, "not new"
            return 0
        print "sendPasswords: OK", "pass=", pw, "hash=", ph, "pow=", thispow
        peerslock.acquire()
        known_pows.add(thispow)
        peerslock.release()
        broadcast_pow(thispow)
        return 1

    def broadcastPOW(self, p, h):
        global known_pows
        peerslock.acquire()
        known_pows.add((p, h))
        peerslock.release()
        broadcast_pow((p, h))
        return False

    def stop(self):
        print '#####ACABANDO'
        global stopFlag
        stopFlag = True
        return False

    def ping(self):
        #print 'PINGANDO'
        return True

#--------------------------------------------------------------
# Server Thread
#--------------------------------------------------------------
class ServerThread(threading.Thread):
    def __init__ (self):
        global node_id
        sys.stdout.write("Creating server " + str(node_id) + "\n")
        sys.stdout.flush()
        threading.Thread.__init__(self)

    def run(self):
        global node_id
        server = SimpleXMLRPCServer.SimpleXMLRPCServer(("localhost", 8000 + node_id))
        server.register_instance(Functions())
        try:
            server.serve_forever()
        except:
            pass

def start_server_thread():
    t = ServerThread()
    t.daemon = True
    t.start()

#--------------------------------------------------------------
# Topology Phase
#--------------------------------------------------------------
def topology_phase():
    global peers
    print "Node", node_id, ": topology phase"
    for tries in range(3):
        time.sleep(1)
        peerslock.acquire()
        p = copy.copy(peers)
        peerslock.release()
        # Tenta pegar mais peers
        for x in p:
            #print node_id, 'calling ', x
            res = False
            try:
                server = xmlrpclib.Server(x)
                res = server.getPeers(list(p))
                server = False
            except:
                pass
            peerslock.acquire()
            try:
                for y in res:
                    peers.add(y)
            except:
                pass
            peerslock.release()
        peerslock.acquire()
        print "Node ", node_id, "peers:", list(peers)
        peerslock.release()

#--------------------------------------------------------------
# GetBreak Phase
#--------------------------------------------------------------
def getbreak_phase():
    global tobreak
    print "Node", node_id, ": getbreak phase"
    for x in peers:
        res = False
        try:
            server = xmlrpclib.Server(x)
            res = server.getHashes()
            server = False
            for y in res:
                tobreak.append((x, y))
            #print "aindadeuerro"
        except:
            print "deuerro"
            pass

#--------------------------------------------------------------
# Break Phase
#--------------------------------------------------------------
def break_phase():
    print "Node", node_id, ": passbreak phase"
    print "Node", node_id, ": tobreak=", tobreak
    chars = string.letters + string.digits
    #for tup in tobreak:             # tup = (server, hash)
    #    server = tup[0]
    #    h = tup[1]
    for base_count in range(3):
        count = base_count + 1
        res = itertools.product(chars, repeat=count)
        for i in res:
            p = ''.join(i)
            m = mkhash(p)
            if m[:3] == '1cd':
                print "Node", node_id, "found pow"
                pows.append( (p, m) )
            for tup in tobreak:
                server = tup[0]
                h = tup[1]
                if m == h:
                    print "Node", node_id, "found pass", p
                    broken.add( (server, p, m) )
    for tup in tobreak:
        server = tup[0]
        h = tup[1]
        for b in broken:
            if h == b[2]:
                pfound = False
                ptouse = False
                for pw in pows:
                    if pw not in known_pows:
                        pfound = True
                        ptouse = pw
                        break
                if pfound:
                    pows.remove(ptouse)
                    arg_ph = (b[1], b[2])
                    arg_pow1 = ptouse[0]
                    arg_pow2 = ptouse[1]
                    print node_id, "Sendpass", b[0], arg_ph, arg_pow1, arg_pow2
                    try:
                        server = xmlrpclib.Server(b[0])
                        res = server.sendPasswords(arg_ph, arg_pow1, arg_pow2)
                    except:
                        pass
            

#--------------------------------------------------------------
# Caller Thread
#--------------------------------------------------------------
class CallerThread(threading.Thread):
    def __init__ (self):
        threading.Thread.__init__(self)

    def run(self):
        topology_phase()
        getbreak_phase()
        break_phase()
        print "Node", node_id, "idle"

def start_caller_thread():
    t = CallerThread()
    t.daemon = True
    t.start()

#--------------------------------------------------------------
# Broadcast Thread
#--------------------------------------------------------------
class BroadcastThread(threading.Thread):
    def __init__ (self):
        threading.Thread.__init__(self)

    def run(self):
        global bcdone
        while True:
            time.sleep(0.3)
            for b in bctodo:
                if not b in bcdone:
                    for x in peers:
                        res = False
                        try:
                            server = xmlrpclib.Server(x)
                            res = server.broadcastPOW(b[0], b[1])
                            server = False
                        except:
                            pass
                    bcdone.append(b)
            pass

def start_bc_thread():
    t = BroadcastThread()
    t.daemon = True
    t.start()

## ===================================================
init_id()
init_hashes()
init_peers()

print list(peers)
print "Node", node_id, "hashes:", hashes

start_server_thread()
start_caller_thread()
start_bc_thread()

while not stopFlag:
    time.sleep(1)

## =========================
