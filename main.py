import sys
from optparse import OptionParser
from coordinator import Coordinator

if __name__=='__main__':
    usage = 'usage: python %prog [options]'
    parser = OptionParser(usage=usage)
    (options, args) = parser.parse_args(sys.argv[1:])
    
    global_coordinator = Coordinator()
