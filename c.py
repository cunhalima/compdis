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
hashlist = server.getHashes()

combs = []

for h in hashlist:
    for count in range(3):
        res = itertools.product(chars, repeat=count+1)
        for i in res: 
            p = ''.join(i)
            m = md5.new(p).hexdigest()
            if m == h:
                combs.append((m, p))

print combs
server.sendPasswords(combs)
