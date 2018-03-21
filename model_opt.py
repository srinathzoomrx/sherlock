'''
model_opt.py module is an updated and optimised version model.py
This module uses graph techniques to identify the relations that
are required to be joined for the successful execution of the
SQL query according to the Natural Language query.
The details of output and input parameters are given in the class model_opt
'''
import networkx as nx
import matplotlib.pyplot as plt
from itertools import chain
from networkx.utils import pairwise
from relation_schema import rel_schema


__all__ = ['metric_closure', 'steiner_tree']


def metric_closure(G, weight='weight'):
    """
    Return the metric closure of a graph.

    The metric closure of a graph 'G' is the complete graph in which each edge
    is weighted by the shortest path distance between the nodes in 'G'.

    Parameters
    ----------
    G : NetworkX graph

    Returns
    -------
    NetworkX graph (Metric closure of the graph 'G').

    """
    M = nx.Graph()

    seen = set()
    Gnodes = set(G)
    for u, (distance, path) in nx.all_pairs_dijkstra(G, weight=weight):
        seen.add(u)
        for v in Gnodes - seen:
            M.add_edge(u, v, distance=distance[v], path=path[v])

    return M


def steiner_tree(G, terminal_nodes, weight='weight'):
    """
    Return an approximation to the minimum Steiner tree of a graph.

    Parameters
    ----------
    G : NetworkX graph

    terminal_nodes : list
        A list of terminal nodes for which minimum steiner tree is
        to be found.

    Returns
    -------
    NetworkX graph
        Approximation to the minimum steiner tree of `G` induced by
        `terminal_nodes` .

    Notes
    -----
    Steiner tree can be approximated by computing the minimum spanning
    tree of the subgraph of the metric closure of the graph induced by the
    terminal nodes, where the metric closure of *G* is the complete graph in
    which each edge is weighted by the shortest path distance between the
    nodes in *G* .
    This algorithm produces a tree whose weight is within a (2 - (2 / t))
    factor of the weight of the optimal Steiner tree where *t* is number of
    terminal nodes.
    """
    M = metric_closure(G, weight=weight)
    # M is the subgraph of the metric closure induced by the terminal nodes of G.
    # Use the 'weight/distance' attribute of each edge provided by the metric closure graph.
    H = M.subgraph(terminal_nodes)
    mst_edges = nx.minimum_spanning_edges(H, weight='distance', data=True)
    # Create an iterator over each edge in each shortest path; repeats are okay
    edges = chain.from_iterable(pairwise(d['path']) for u, v, d in mst_edges)
    T = G.edge_subgraph(edges)
    return T


class model_opt:
    G = nx.Graph()

    def __init__(self):
        edge_list = [
            ('teams', 'players', 1),
            ('innings', 'overs', 1),
            ('innings', 'matches', 1),
            ('innings', 'teams', 1),
            ('matches', 'teams', 1),
            ('matches', 'players', 1),
            ('matches', 'stadiums', 1),
            ('overs', 'players', 1),
            ('overs', 'balls', 1),
            ('balls', 'wickets', 1),
            ('players', 'balls', 1),
            ('players', 'wickets', 1),
            ('players', 'batsman', 1),
            ('players', 'bowler', 1),
            ('matches', 'batsman', 1),
            ('matches', 'bowler', 1)]
        self.G.add_weighted_edges_from(edge_list)

    def getPathRelations(self, terminal_nodes):
        '''
        getPathRelations() function to implement the graph algorithms
        inputs: A list of relations names that are compulsory for the query processing.
        output: A list of join conditions for the joining the relations.
        '''
        ret_relations = []

        if(len(terminal_nodes) <= 1):
            ret_relations = terminal_nodes
            ret_relations.append(None)
            ret_relations = [ret_relations]
        else:
            T = steiner_tree(self.G, terminal_nodes)
            plt.subplot(121)
            join_list = list(nx.bfs_edges(T, terminal_nodes[0]))
            for i in range(len(join_list)):
                left_rel = join_list[i][0]
                right_rel = join_list[i][1]
                condtion_ele = rel_schema[left_rel][0]['related'][right_rel]
                if(isinstance(condtion_ele, list)):
                    condtion_ele = condtion_ele[0]
                ele = [left_rel, right_rel, condtion_ele]
                ret_relations.append(ele)
            # nx.draw(T, with_labels=True)
            # plt.show()
        return ret_relations


def main():
    M = model_opt()
    relations = M.getPathRelations(['stadiums', 'overs'])
    print "\n***** Join Conditions *****\n\n"
    for i in range(len(relations)):
        print relations[i]
        print
    print "\n\n*************************\n\n"
    query = ""
    if(relations[0][1] is None):
        query = relations[0][0]
    else:
        for relation in relations:
            query = query + '('
        query = query + relations[0][0]
        for relation in relations:
            query = query + "\nINNER JOIN " + relation[1] + " ON " + relation[2]
            query = query + ')'

    print query


if __name__ == '__main__':
    main()
