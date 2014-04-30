#!/usr/bin/python
import xmlrpclib
import sys

print "Parando"
for i in range(int(sys.argv[1])):
    j = i + 8000
    try:
        server = xmlrpclib.Server('http://localhost:' + str(j))
        server.stop()
    except:
        pass
