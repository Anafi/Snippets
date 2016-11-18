
# source: http://stackoverflow.com/questions/3277367/how-does-pythons-super-work-with-multiple-inheritance
class First(object):
    def __init__(self):
        print "first"

class Second(First):
    def __init__(self):
        print "second"

class Third(First):
    def __init__(self):
        print "third"

class Fourth(Second, Third):
    def __init__(self):
        super(Fourth, self).__init__()
        print "that's it"



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