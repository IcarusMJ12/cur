#!/usr/bin/env python

"""
Count Ur Redundancies, or maybe Cleanup Ur Repo! (using DAWG)

Finds oc-CUR-rences of maximal repeats in ur code.
"""

from os.path import basename

import argparse
from termcolor import colored

from strie import STrie

def canonize(line):
    return line.strip(' \r\n\t{}')

class Analyzer(object):
    def __init__(self):
        self.canonized = {}
        self.lines = []
        self.lineno_map = []
        self.trie = STrie()
        self.nodes_added = 0

    def add(self, filename):
        elements = []
        lineno_map = {}
        actual_index = 0
        canonical_index = 0
        with open(filename, 'r') as f:
            for line in f:
                canonical_line = canonize(line)
                canonical_hash = hash(canonical_line)
                self.canonized[canonical_hash] = canonical_line
                if canonical_line != '':
                    elements.append(canonical_hash)
                    lineno_map[canonical_index] = actual_index
                    canonical_index += 1
                actual_index += 1
        self.lines.append(elements)
        self.lineno_map.append(lineno_map)
        return self.trie.add(elements)
    
def main():
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument('-l', '--length', type=int, default=3,\
            help="minimum repeat length to consider")
    parser.add_argument('-c', '--count', type=int, default=3,\
            help="minimum number of repeats to consider")
    parser.add_argument("file", nargs='+', help="source file to analyze")
    args = parser.parse_args()
    filenames = args.file
    a = Analyzer()
    total = 0
    for filename in filenames:
        print "processing", filename, "...",
        node_count = a.add(filename)
        print node_count, "nodes added"
        total += node_count
    print "total nodes:", total
    repeats = sorted(a.trie.maximal_repeats(),\
            lambda x, y: cmp(x.length, y.length), reverse=True)
    for repeat in repeats:
        print colored('%d repeats of length %d' % (len(repeat.indices),\
                repeat.length), 'white', 'on_red')
        indices = '@ '
        for index in repeat.indices:
            indices += '(%s,%d) ' % (basename(filenames[index[0]]),\
                    a.lineno_map[index[0]][index[1] - repeat.length + 1] + 1)
        print colored(indices, 'white', 'on_red')
        index = iter(repeat.indices).next()
        for i in xrange(index[1] - repeat.length + 1, index[1] + 1):
            print '\t', a.canonized[a.lines[index[0]][i]]

if __name__ == '__main__':
    main()
