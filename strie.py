#!/usr/bin/env python
"""
A sample implementation of Ukkonen's suffix trie.
"""

class MaximalRepeat(object):
    def __init__(self, strings, length, indices):
        self.strings, self.length, self.indices = strings, length, indices
    
    def __repr__(self):
        index = iter(self.indices).next()
        string = self.strings[index[0]][index[1] - self.length + 1:index[1] + 1]
        return '<' + str(list(self.indices)) + ':' + string + '>'

class Node(object):
    def __init__(self, index, suffix_link=None):
        self.indices = set([index])
        self._children = {}
        # stores the keys longest edge first
        self._children_keys = []
        self.suffix_link = suffix_link
    
    def __getitem__(self, index):
        return self._children[index]

    def __setitem__(self, index, val):
        if index not in self._children.keys():
            self._children_keys.append(index)
        self._children[index] = val
    
    def keys(self):
        return self._children_keys

class STrie(object):
    def __init__(self):
        self.root = Node(None)
        self.strings = []
        self.nodes_added = 0

    def add(self, string):
        self.nodes_added = 0
        self.strings.append(string)
        string_index = len(self.strings) - 1
        current = self.root
        for i in xrange(len(string)):
            current = self._insert((string_index, i), current)
        self._insert((string_index, len(string)), current)
        return self.nodes_added
    
    def _insert(self, index, node):
        try:
            key = self.strings[index[0]][index[1]]
        except IndexError:
            key = index
        if key in node.keys():
            n = node[key]
            while n.suffix_link is not None:
                n.indices.add(index)
                n = n.suffix_link
            return node[key]
        if node.suffix_link is None:
            child = Node(index, node)
        else:
            child = Node(index, self._insert(index, node.suffix_link))
        node[key] = child
        self.nodes_added += 1
        return child

    def maximal_repeats(self, cutoff_repeats=3, cutoff_length=3):
        result = []
        seen = {}
        for key in self.root.keys():
            ret = [r for r in self._maximal_repeats_r(self.root[key])\
                    if min(r.indices) not in seen.keys() or\
                    len(r.indices) > seen[min(r.indices)]]
            for r in ret:
                seen[min(r.indices)] = len(r.indices)
            result += ret
        return [r for r in result\
                if len(r.indices) >= cutoff_repeats and r.length >= cutoff_length]

    def _maximal_repeats_r(self, node, length=1):
        len_keys = len(node.keys())
        if len_keys == 0:
            return [MaximalRepeat(self.strings, length, node.indices)]
        if len_keys == 1:
            return self._maximal_repeats_r(node[node.keys()[0]], length + 1)
        result = []
        for key in node.keys():
            result += self._maximal_repeats_r(node[key], length + 1)
        result += [MaximalRepeat(self.strings, length, node.indices)]
        return result
    
if __name__ == '__main__':
    import argparse
    import pygraphviz as pgv

    def render_node_r(node, strings, graph):
        try:
            index = node.indices.pop()
            node.indices.add(index)
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
            #print node.indices, '->', node[key].indices
        if suffix_link is not None:
            try:
                index = suffix_link.indices.pop()
                suffix_link.indices.add(index)
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
                help="String to render the suffix trie of into a 'result.png'.")
        args = parser.parse_args()
        trie = STrie()
        for string in args.string:
            print trie.add(string), 'nodes added'
        result = render_trie(trie)
        result.layout('dot')
        result.draw(''.join(args.string) + '-strie.png')
        repeats = trie.maximal_repeats(3, 3)
        for r in repeats:
            print r

    main()
