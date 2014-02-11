#!/usr/bin/env python
"""
A sample implementation of Ukkonen's suffix trie.
"""

from sys import getsizeof

__all__ = ['MaximalRepeat', 'Node', 'STrie']

class MaximalRepeat(object):
    """
    A struct-like object for maximal repeat metadata.
    """
    __slots__ = ('strings', 'length', 'indices', 'contains')

    def __init__(self, strings, length, indices, contains=None):
        """
        `strings` is an array of strings where the maximal repeat is found.
        `length` is the length of this repeat.
        `indices` are the offsets in `strings` to the *last* element of the repeat.
        `contains` is a reference to a contained smaller but more frequent repeat.
        """
        self.strings, self.length, self.indices, self.contains =\
                strings, length, indices, contains
    
    def __repr__(self):
        index = iter(self.indices).next()
        string = self.strings[index[0]][index[1] - self.length + 1:index[1] + 1]
        return '<' + str(list(self.indices)) + ':' + string + '>'

class Node(object):
    """
    A suffix trie node.
    """
    __slots__ = ('_indices', '_children', 'suffix_link')

    def __init__(self, index, suffix_link=None):
        """
        `index` is the 2-tuple position of this node in the suffix trie.
        """
        # not using set because set takes up entirely too much memory
        self._indices = index
        self._children = None
        self.suffix_link = suffix_link
    
    def size(self):
        return getsizeof(self._indices) + getsizeof(self._children) + getsizeof(self)

    def update_index(self, index):
        if not isinstance(self._indices, list) and self._indices != index:
            self._indices = [self._indices, index]
        elif index not in self._indices:
            self._indices.append(index)
    
    @property
    def index_len(self):
        if isinstance(self._indices, list):
            return len(self._indices)
        if self._indices is not None:
            return 1
        return 0

    @property
    def first_index(self):
        if isinstance(self._indices, list):
            return self._indices[0]
        if self._indices is not None:
            return self._indices
        raise TypeError()

    @property
    def indices(self):
        if isinstance(self._indices, list):
            return tuple(sorted(self._indices))
        return tuple([self._indices])

    def __getitem__(self, index):
        if self._children is not None:
            if isinstance(self._children, dict):
                return self._children[index]
            if self._children[0] == index:
                return self._children[1]
        raise KeyError(index)

    def __setitem__(self, index, val):
        if self._children is not None:
            if isinstance(self._children, dict):
                self._children[index] = val
                return
            if self._children[0] == index:
                self._children = (index, val)
                return
            self._children = { self._children[0]: self._children[1], index: val }
        else:
            self._children = (index, val)
    
    def keys(self):
        if self._children is not None:
            if isinstance(self._children, dict):
                return self._children.keys()
            return (self._children[0],)
        return ()

class STrie(object):
    """
    A suffix trie.
    """
    __slots__ = ('root', 'strings', 'nodes_processed', 'current', '_root_keys',\
            'size')

    def __init__(self):
        self.root = Node(None)
        self.strings = []
        self.nodes_processed = 0
        self.current = None
        self._root_keys = []
        self.size = 0

    def add(self, string):
        """
        Call this for each string you wish to add to the same trie.
        """
        self.nodes_processed = 0
        self.strings.append(string)
        string_index = len(self.strings) - 1
        self.current = self.root
        for i in xrange(len(string)):
            if string[i] not in self.root.keys():
                self._root_keys.append(string[i])
            for count in self._insert((string_index, i)):
                yield count
        for count in self._insert((string_index, len(string))):
            yield count
        yield self.nodes_processed
    
    def _insert(self, index):
        try:
            key = self.strings[index[0]][index[1]]
        except IndexError:
            key = index
        current, last_inserted = self.current, None
        while current is not None:
            child = None
            if key in current.keys():
                n = current[key]
                while n.suffix_link is not None:
                    n.update_index(index)
                    n = n.suffix_link
                child = current[key]
            elif current.suffix_link is None:
                child = Node(index, current)
                self.size += child.size()
            else:
                child = Node(index)
                self.size += child.size()
            if last_inserted is not None:
                last_inserted.suffix_link = child
            current[key] = child
            current, last_inserted = current.suffix_link, child
            self.nodes_processed += 1
            if self.nodes_processed % 1000 == 0:
                yield self.nodes_processed
        self.current = self.current[key]

    def maximal_repeats(self,\
            cutoff_metric = lambda count, length: int(count >= 3 and length >= 3)):
        """
        Returns maximal repeats where the count and length of the repeat are
        greater than the provided cutoff metric as determined by the provided
        `cutoff_metric` function taking count and length as arguments, respectively.
        """
        ret = []
        seen = {}
        for key in self._root_keys:
            result = []
            stack = [(self.root[key], 1, None)]
            while len(stack) != 0:
                node, length, contains = stack.pop()
                len_keys = len(node.keys())
                if len_keys == 0 and cutoff_metric(node.index_len, length) > 0\
                        and (node.first_index not in seen.keys() or\
                        node.index_len > seen[node.first_index]):
                    result.append(MaximalRepeat\
                            (self.strings, length, node.indices, contains))
                elif len_keys == 1:
                    stack.append( (node[node.keys()[0]], length + 1, contains) )
                else:
                    if (node.first_index not in seen.keys() or\
                            node.index_len > seen[node.first_index]) and\
                            cutoff_metric(node.index_len, length) > 0:
                        contains = MaximalRepeat(self.strings, length, node.indices, contains)
                        result.append(contains)
                    for key in node.keys():
                        stack.append( (node[key], length + 1, contains) )
            seen.update([(min(r.indices), len(r.indices)) for r in result])
            ret += result
        return ret
    
if __name__ == '__main__':
    import argparse
    from sys import stdout

    import pygraphviz as pgv

    def render_node_r(node, strings, graph):
        try:
            index = node.first_index
            label = strings[index[0]][index[1]]
        except IndexError:
            label = '<eof>'
        except TypeError:
            label = '<root>'
        suffix_link = node.suffix_link
        node_id = id(node)
        graph.add_node(node_id, label=label)
        keys = node.keys()
        for key in keys:
            render_node_r(node[key], strings, graph)
            graph.add_edge(node_id, id(node[key]))
        if suffix_link is not None:
            try:
                index = suffix_link.first_index
                suffix_label = strings[index[0]][index[1]]
            except IndexError:
                suffix_label = '<eof>'
            except TypeError:
                suffix_label = '<root>'
            graph.add_node(id(suffix_link), label=suffix_label)
            graph.add_edge(node_id, id(suffix_link), color='gray',
                    constraint=False)

    def render_trie(trie):
        graph = pgv.AGraph(directed=True)
        graph.graph_attr['label'] = "Suffix Trie for '%s'" % trie.strings
        graph.node_attr['shape'] = 'circle'
        render_node_r(trie.root, trie.strings, graph)
        return graph

    def main():
        parser = argparse.ArgumentParser(description = __doc__)
        parser.add_argument("string", nargs='+',
                help="String to render the suffix trie of")
        args = parser.parse_args()
        trie = STrie()
        for string in args.string:
            print string
            for count in trie.add(string):
                stdout.write('\r\t%d nodes processed' % count)
                stdout.flush()
            stdout.write('\n')
        result = render_trie(trie)
        result.layout('dot')
        result.draw(''.join(args.string) + '-strie.png')
        repeats = sorted(trie.maximal_repeats(\
                lambda repeats, length: repeats >= 3 and length >= 3),\
                lambda x, y: cmp(x.length, y.length), reverse=True)
        for r in repeats:
            print r

    main()
