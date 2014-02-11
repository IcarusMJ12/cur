#!/usr/bin/env python

"""
Count Ur Redundancies, or maybe Cleanup Ur Repo! (using DAWG) finds
oc-CUR-rences of maximal repeats in ur code.

The default metric is chosen with the assumption that one would refactor C++
code formatted using google style, i.e. cuddled braces.
Thus, count-1 is chosen because only one instance of copypasta will remain,
length-1 because the copypasta will be replaced by a function call, and there's
2 extra overhead assumed for the function call signature and the closing brace.
"""

__all__ = ['Analyzer']

from os.path import basename
from sys import stdout

import argparse
from termcolor import colored

from strie import STrie

DEFAULT_METRIC = '(c-1)*(l-1)-2'
ALLOWED_METRIC_CHARS = set(' cl0123456789%^*()-+/')

CUR_FILENAME = '.cur.rent'

colored_red = lambda x: colored(x, 'white', 'on_red') if stdout.isatty() else x

def canonize(line):
    """
    A rudimentary C/C++ line canonizer that strips whitespace and squiggly
    brackets
    """
    return line.strip(' \r\n\t{}')

class Analyzer(object):
    """
    Adds hash representations of file lines to a suffix trie and generates
    maximal pairs.
    """

    def __init__(self, canonize):
        """
        Takes a `canonize` function that strips the cruft from a line of source code
        for the purpose of comparison to other lines.
        """
        self.canonized = {}
        self.lines = []
        self.lineno_map = []
        self._trie = STrie()
        self.lines_count = 0
        self.canonize = canonize

    def add(self, filename):
        """
        This should be called for each source file you wish to add to the same
        suffix tree.
        """
        elements = []
        lineno_map = {}
        actual_index = 0
        canonical_index = 0
        with open(filename, 'r') as f:
            for line in f:
                canonical_line = self.canonize(line)
                canonical_hash = hash(canonical_line)
                self.canonized[canonical_hash] = canonical_line
                if canonical_line != '':
                    elements.append(canonical_hash)
                    lineno_map[canonical_index] = actual_index
                    canonical_index += 1
                actual_index += 1
        self.lines.append(elements)
        self.lineno_map.append(lineno_map)
        self.lines_count += actual_index
        for count in self._trie.add(elements):
            yield count
    
    def get_sorted_repeats(self, metric):
        """
        Returns maximal repeats sorted according to the provided severity metric
        function.  The metric function takes repeat count and repeat length as its
        two inputs, respectively.
        """
        return sorted(self._trie.maximal_repeats(metric), lambda x,y:\
                cmp(metric(len(x.indices), x.length), metric(len(y.indices),\
                y.length)), reverse=True)
    
def main():
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument('-m', '--metric', default=DEFAULT_METRIC,\
            help="a severity metric lambda for maximal repeat (c)ount and (l)ength" +\
            ", defaults to '%s'" % DEFAULT_METRIC)
    parser.add_argument("file", nargs='+', help="source file to analyze")
    args = parser.parse_args()
    filenames, metric = args.file, args.metric
    for c in metric:
        assert c in ALLOWED_METRIC_CHARS, "metric characters must be in '%s'" %\
                ''.join(list(ALLOWED_METRIC_CHARS))
    metric = eval("lambda c, l: " + metric, None, None)
    a = Analyzer(canonize)
    total = 0
    for filename in filenames:
        print "processing", filename, "..."
        stdout.flush()
        node_count = 0
        for node_count in a.add(filename):
            if stdout.isatty():
                stdout.write('\r\t%d nodes processed' % node_count)
                stdout.flush()
        total += node_count
        stdout.write('\n')
    print "total nodes:", total
    print "finding maximal repeats (this may take a while)"
    repeats = a.get_sorted_repeats(metric)
    total_severity = 0
    for repeat in repeats:
        severity = metric(len(repeat.indices), repeat.length)
        contains = repeat.contains
        if contains is None:
            total_severity += severity
        else:
            total_severity += max(0,\
                    metric(len(repeat.indices), repeat.length - contains.length + 1))
        print colored_red(\
                'severity %d: %d repeats of length %d; id %d, contains %d' %\
                (severity, len(repeat.indices), repeat.length, id(repeat),\
                id(contains) if contains is not None else 0))
        indices = '@ '
        for index in repeat.indices:
            indices += '(%s,%d) ' % (basename(filenames[index[0]]),\
                    a.lineno_map[index[0]][index[1] - repeat.length + 1] + 1)
        print colored_red(indices)
        index = iter(repeat.indices).next()
        for i in xrange(index[1] - repeat.length + 1, index[1] + 1):
            print '\t', a.canonized[a.lines[index[0]][i]]
    print colored_red('%d/%d lines can be refactored' %\
            (total_severity, a.lines_count))
    try:
        with open(CUR_FILENAME, 'rb') as f:
            print colored_red('last run it was %s/%s lines' %\
                    tuple(f.read().strip().split('/')))
    except IOError as e:
        if e.errno != 2: # 2 is file does not exist
            raise
    with open(CUR_FILENAME, 'wb') as f:
        f.write('%d/%d' % (total_severity, a.lines_count))

if __name__ == '__main__':
    main()
