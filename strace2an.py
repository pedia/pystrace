# -*- coding: utf8 -*-

try:
    import counter
    Counter = counter.Counter
except:
    import collections
    Counter = collections.Counter

import getopt
import os.path
import sys

from strace import *
from strace_utils import *

def mid(t, a, b):
    """
    >>> mid('abc', 'a', 'b')
    ''
    >>> mid('abcde', 'b', 'd')
    'c'
    >>> mid('abcde', 'a', 'd')
    'bc'
    >>> mid('abc', 'a', 'c')
    'b'
    >>> mid('ab', 'a', 'b')
    ''
    >>> mid('ab', 'a', 'd')
    >>> mid('ab', 'c', 'd')
    >>> mid('PATH_INFO/\\0/topic/praise/23080929/budejie-win-1.2/0-5.json\\r\\0', 'PATH_INFO/\\0', '\\r')
    '/topic/praise/23080929/budejie-win-1.2/0-5.json'
    """
    ia = t.find(a)
    if -1 != ia:
        ia += len(a)
        ib = t.find(b, ia)
        if -1 != ib:
            return t[ia : ib]
    return None

class Request(object):
    def __init__(self, uri, timestamp):
        self.uri = uri
        self.begin = timestamp
        self.finish = None
        self.counter = Counter()

    def incr(self, type):
        self.counter[type] += 1

    def dump(self, timestamp):
        diff = timestamp - self.begin
        if diff > 1:
            print diff, self.uri, 'SLOW'
        else:
            print diff, self.uri
        for key, val in self.counter.iteritems():
            print "%8d %s" % (val, key)
        print ''


def inlist(s, l):
    for i in l:
        if s in i:
            return True
    return False

def analysis(input_file, output_file=None, separator=',', quote='"'):
    # Open the files

    if input_file is not None:
        f_in = open(input_file, "r")
    else:
        f_in = sys.stdin

    if output_file is not None:
        f_out = open(output_file, "w")
    else:
        f_out = sys.stdout

    # Process the file

    strace_stream = StraceInputStream(f_in)
    first = True
    request_begin = False
    req = None

    for entry in strace_stream:
        if first:
            first = False

        # # Print

        # if entry.was_unfinished:
        #     i_was_unfinished = 1
        # else:
        #     i_was_unfinished = 0

        # data = [entry.timestamp, entry.syscall_name, entry.category, i_was_unfinished,
        #         len(entry.syscall_arguments), array_safe_get(entry.syscall_arguments, 0),
        #         array_safe_get(entry.syscall_arguments, 1),
        #         array_safe_get(entry.syscall_arguments, 2),
        #         array_safe_get(entry.syscall_arguments, 3),
        #         array_safe_get(entry.syscall_arguments, 4),
        #         array_safe_get(entry.syscall_arguments, 5), entry.return_value, entry.elapsed_time]
        # if strace_stream.have_pids:
        #     data.insert(0, entry.pid)
        # csv_write_row_array(f_out, data, separator, quote)
        
        if req is None and entry.syscall_name == 'read':
            for a in entry.syscall_arguments:
                if 'REQUEST_URI' in a:
                    # request_begin = True
                    # print a
                    uri = mid(a, 'PATH_INFO', '\\r')
                    # assert uri
                    if not uri:
                        print 'path info failed:', a
                    uri = uri[uri.find('\\0') + 2:]

                    req = Request(uri, entry.timestamp)

        if req:
            if entry.syscall_name == 'close' and entry.syscall_arguments == ['6', ]:
                req.dump(entry.timestamp)
                req = None
                continue

            if entry.syscall_name == 'sendto':
                if inlist('HGETALL', entry.syscall_arguments):
                    req.incr('redit.getall')
                elif inlist('HGET', entry.syscall_arguments):
                    req.incr('redis.get')
                elif inlist('get ', entry.syscall_arguments):
                    req.incr('cache.get')
            elif entry.syscall_name == 'write':
                if inlist('SELECT ', entry.syscall_arguments):
                    req.incr('db.select')
            elif entry.syscall_name == 'connect':
                req.incr('connect')
            elif entry.syscall_name == 'stat':
                req.incr('stat')



    # Close the files

    if f_out is not sys.stdout:
        f_out.close()
    strace_stream.close()


#
# Print the usage information
#
def usage():
    sys.stderr.write('Usage: %s [OPTIONS] [FILE]\n\n' % os.path.basename(sys.argv[0]))
    sys.stderr.write('Options:\n')
    sys.stderr.write('  -h, --help         Print this help message and exit\n')
    sys.stderr.write('  -o, --output FILE  Print to file instead of the standard output\n')


#
# The main function
#
# Arguments:
#   argv - the list of command-line arguments, excluding the executable name
#
def main(argv):

    input_file = None
    output_file = None

    # Parse the command-line options

    try:
        options, remainder = getopt.gnu_getopt(argv, 'ho:', ['help', 'output='])

        for opt, arg in options:
            if opt in ('-h', '--help'):
                usage()
                return
            elif opt in ('-o', '--output'):
                output_file = arg

        if len(remainder) > 1:
            raise Exception("Too many options")
        elif len(remainder) == 1:
            input_file = remainder[0]
    except Exception as e:
        sys.stderr.write("%s: %s\n" % (os.path.basename(sys.argv[0]), e))
        sys.exit(1)

    # Convert to .csv

    try:
        analysis(input_file, output_file)
    except IOError as e:
        sys.stderr.write("%s: %s\n" % (os.path.basename(sys.argv[0]), e))
        sys.exit(1)

#
# Entry point to the application
#
if __name__ == "__main__":
    main(sys.argv[1:])
