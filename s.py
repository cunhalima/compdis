#!/usr/bin/python
import SimpleXMLRPCServer
import md5

hashes = [ md5.new("aB").hexdigest(), md5.new("b").hexdigest() ]

class Functions:

    def getHashes(self):
        return hashes

    def sendPasswords(self, res):
        print "Found: ", res
        return False

server = SimpleXMLRPCServer.SimpleXMLRPCServer(("localhost", 8000))
server.register_instance(Functions())
server.serve_forever()
