
from PyQt4.QtCore import QObject
#class First(object):
#    def __init__(self):
#        print "first"

class Second(QObject):
    def __init__(self):
        QObject.__init__(self)
        print "second"

class Third():
    def __init__(self):
        #QObject.__init__(self)
        print "third"
    def run(self):
        print "methods inhereted"

class Fourth(Second, Third):
    def __init__(self):
        super(Fourth, self).__init__()
        print "that's it"