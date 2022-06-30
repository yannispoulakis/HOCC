import pandas as pd
import os
from franz.openrdf.connect import ag_connect


# First Queries
class resource_query_routine:
    def __init__(self):
        self.clusters_df = ""
        self.clusters_nodes_df = ""
        self.aggregated_df = ""
        self.conn = ""
        pass

    def connect_to_allegro_repository(self):
        self.conn = ag_connect('repo5', host=os.environ.get('AGRAPH_HOST'), port=10035,
                          user='test', password='xyzzy')

    def describe_clusters(self):
        """Retrieve for the clusters in the ontology the following properties:
           - Platform, Energy, Resilience Score
           - Number of cluster nodes
           - Platform name and distribution that the cluster is based on
           - Cluster id
           - Cluster Locality
        """

        query_1 = """
                    PREFIX :      <http://www.physics-h2020.eu/physics/resources_ontology#>
                    SELECT  ?name ?cplatform ?Energy ?Resilience ?Performance ?type
                    WHERE {?name rdf:type :Cluster .
                           ?name :usesPlatform ?cplatform .
                           ?name :hasEnergyScore ?Energy .
                           ?name :hasResilienceScore ?Resilience .
                           ?name :hasPerformanceScore ?Performance .   
                           ?name :hasLocality    ?type . 
                   }
                   """

        query_2 = """
                    PREFIX :      <http://www.physics-h2020.eu/physics/resources_ontology#>
                    SELECT  ?name  (COUNT(?node) AS ?nodes)
                    WHERE {?name rdf:type :Cluster .  
                           ?node :isPartOfCluster ?name .
                   }
                   GROUP BY ?name"""

        df1 = self.conn.executeTupleQuery(query_1).toPandas()
        df2 = self.conn.executeTupleQuery(query_2).toPandas()
        print(df1)
        print(df2)
        # Platform name , platform distribution, cluster id
        df = df1.merge(df2, on="name")
        df["platform"] = "kubernetes"

        df["platform distribution"] = df.cplatform.values[0].split("#")[-1].replace(">", "")
        df["id"] = df.name.values[0].split("#")[-1].replace(">", "")
        self.clusters_df = df
        return df

    def describe_cluster_nodes(self):
        """Retrieve information about each clusters nodes. Specifically retrieve the ram/cpu values."""

        query_1 = """
                    PREFIX :      <http://www.physics-h2020.eu/physics/resources_ontology#>
                    SELECT ?name  ?ram ?cpu ?ramvalue ?cpuvalue ?architecture
                    WHERE
                       {?name       rdf:type                                 :Cluster.
                        ?node       :isPartOfCluster                         ?name.
                        ?node       :hasRawComputationalResource             ?ram.
                        ?ram        rdf:type                                 :Ram .
                        ?ram        :withAllocatableValue                    ?ramvalue.
                        ?node       :hasRawComputationalResource             ?cpu.
                        ?node       :hasArchitecture                         ?architecture .
                        ?cpu        rdf:type                                 :CPU . 
                        ?cpu        :withCapacityValue                       ?cpuvalue.
                        }"""

        df = self.conn.executeTupleQuery(query_1).toPandas()
        df.replace("Ki", "", regex=True, inplace=True)
        df.ramvalue = (df.ramvalue.astype(int) * 0.001024).astype(int)  # Ki to Mb
        df.cpuvalue = df.cpuvalue.astype(int)
        self.clusters_nodes_df = df
        return df

    def aggregate_results(self):
        architectures = list(self.clusters_nodes_df["architecture"].values)


        self.clusters_nodes_df = self.clusters_nodes_df.groupby("name").sum().reset_index()
        print(architectures)
        if architectures.count(architectures[0]) == len(architectures):
            self.clusters_nodes_df["architecture"] = architectures[0]
        else:
            self.clusters_nodes_df["architecture"] = architectures

        self.aggregated_df = pd.concat([self.clusters_nodes_df, self.clusters_df], axis=1)
        self.aggregated_df.rename(columns={"ramvalue": "memory_in_MB", "cpuvalue": "nb_cpu"}, inplace=True)

        # Add cluster names
        cluster_name_list = []

        for i in range(1, len(self.aggregated_df) + 1):
            cluster_name_list.append("Cluster_{}".format(str(i)))

        self.aggregated_df["ClusterNames"] = cluster_name_list

        return self.aggregated_df

    def transform_to_json(self):
        d = {}
        f = {}
        for i, row in self.aggregated_df.iterrows():
            d2 = {}
            d3 = {}
            d4 = {}



            # d3 = objective scores
            d3['Energy'] = row['Energy']
            d3['Availability'] = row['Resilience']
            d3['Performance'] = row['Performance']

            # d4 = resources
            d4['nb_cpu'] = row['nb_cpu']
            d4['memory_in_MB'] = row['memory_in_MB']

            # d2 = Main cluster characteristics
            d2['id'] = row['id']
            d2['type'] = row['type']
            d2['resources'] = d4
            d2['architecture'] = row['architecture']
            d2['objective_scores'] = d3


            d[row['ClusterNames']] = d2
        f['platform']= d
        return f

    def apply_routine(self):
        self.connect_to_allegro_repository()
        self.describe_clusters()
        self.describe_cluster_nodes()
        self.aggregate_results()
        f = self.transform_to_json()
        return f


if __name__ == "__main__":
    t = resource_query_routine()
    print(t.clusters_df)
    s = t.apply_routine()
    print(s)
