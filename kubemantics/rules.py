from owlready2 import default_world


class semantic_rules:
    def __init__(self, onto):
        self.onto = onto
        self.find_cluster = """
                        PREFIX vocab:      <http://www.physics-h2020.eu/physics/resources_ontology#>

                        SELECT ?s 
                        WHERE {?s a vocab:Cluster .}"""

        pass

    def locality_rule(self):
        qres = default_world.sparql(self.find_cluster)
        for row in qres:
            cluster = row[0]
            if all("arm" in node.hasArchitecture[0].lower() for node in
                    cluster.consistsOfNodes):
                cluster.hasLocality = "edge"

            elif any("arm" in node.hasArchitecture[0].lower() for node in
                             cluster.consistsOfNodes):
                cluster.hasLocality = "hybrid"
            else:
                cluster.hasLocality = "cloud"


