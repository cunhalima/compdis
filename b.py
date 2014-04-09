#!/usr/bin/python


# <string> getHashes()
# Bool sendPasswords((<hash>, <password>), ...)

import xmlrpclib
import md5
import string
import itertools

chars = string.letters + string.digits
server = xmlrpclib.Server('http://localhost:8000')

print "Pedindo hashes"


try:
    server.matar()
except:
    print "opa"

