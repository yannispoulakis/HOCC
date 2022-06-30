import os
import json
import pandas as pd
import numpy as np
from rdflib import Graph, URIRef, Literal
from owlready2 import destroy_entity, get_ontology


def prepare_resources(ontology, individuals, format):
    output = ontology + "__individuals.json"
    graph = Graph().parse(ontology, format=format)
    individuals = [x.name for x in individuals]

    columns = ['s', 'p', 'o']
    c = 0
    data = []
    for s, p, o in graph:
        values = [s, p, o]
        zipped = zip(columns, values)
        d = dict(zipped)
        data.append(d)
    df = pd.DataFrame(data)

    df['spo'] = np.empty
    for index, row in df.iterrows():
        row['spo'] = [row['s'], row['p'], row['o']]

    drop_ind = []
    for index, row in df.iterrows():
        d = False
        for i in individuals:

            for value in row["spo"]:
                if i in value or "type" in value:
                    d = True
        if not d:
            drop_ind.append(index)
    df.drop(set(drop_ind), inplace=True)
    df.reset_index(inplace=True)
    df = df.drop(columns=['index', 'spo'])

    df.head(5)

    g = Graph()
    for index, row in df.iterrows():
        s = URIRef(row['s'])
        p = URIRef(row['p'])
        if 'http' in row['o']:
            o = URIRef(row['o'])
        else:
            o = Literal(row['o'])
        g.add((s, p, o))

        # save the new graph
    g.serialize(destination=output, format='json-ld')

