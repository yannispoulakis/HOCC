import json

from owlready2 import destroy_entity, get_ontology, default_world
import uuid

class kube2onto:

    def __init__(self, onto_path="resource_ontology.owl", cluster_id=""):
        self.onto = get_ontology(onto_path).load()
        self.kubernetes_offerings = ["minikube", "k3", "kind", "minishift", "openshift", "kubeedge"]
        self.cluster_id = cluster_id

    def nodes_to_individuals(self, listed_nodes):
        print("Starting transformation to individuals")
        node = [node for node in listed_nodes["items"]][0]
        # Cluster individual
        if self.cluster_id == "":
            cluster_id = str(uuid.uuid1())
            self.cluster_id = cluster_id
        else:
            pass
        ct = self.onto.Cluster(self.cluster_id)

        # Cloud Platform
        plt = ""
        for term in self.kubernetes_offerings:
            # if more than one of the platforms appear in labels/annotations
            # the last one will apply. This needs fixing.
            if term in node["metadata"]["labels"].keys() or term in node["metadata"]["annotations"].keys():
                plt = self.onto.CloudPlatform(term)
                temp_term = term
            else:
                plt = self.onto.CloudPlatform("k8s")
                temp_term = term

            if temp_term in ["K3s", "kubeedge"]:
                ct.hasEnergyScore = 60
                ct.hasResilienceScore = 10
                ct.hasPerformanceScore = 20
            else:
                ct.hasEnergyScore = 40
                ct.hasResilienceScore = 15
                ct.hasPerformanceScore = 30

        # Cloud Platform characteristics
        ct.usesPlatform = plt

        """Main Part of the function """
        nd_list = []
        for idx, node in enumerate(listed_nodes["items"]):
            # Declare node individual and assign it to cluster individual.
            nd = self.onto.ClusterNode(self.cluster_id + "-node-" + str(idx))
            nd.isPartOfCluster = ct
            nd_list.append(nd)
            # Assign Role to the node (Master/Worker)
            if "node-role.kubernetes.io/worker" in node["metadata"]["labels"].keys():
                nd.hasRole = "Worker"
            else:
                nd.hasRole = 'Master'

            # Node Operating System and Image
            ops = self.onto.OperatingSystem()
            ops.hasImage = node["status"]["nodeInfo"]["osImage"]
            nd.operatesWith = ops
            node_architecture = node["status"]["nodeInfo"]["architecture"]
            nd.hasArchitecture = node_architecture

            # Check labels for known cloud provider.
            cp = ""
            for term in ["aws", "aks", "gke"]:
                if term in node["metadata"]["labels"].keys() or term in node["metadata"]["annotations"].keys():
                    cp = self.onto.CloudProvider(term)

            if "arm" in node_architecture.lower():
                host = self.onto.SingleBoardUnit("Raspberry_" + str(idx))
            else:
                host = self.onto.VirtualResourceUnit("VMNode_" + str(idx))

            nd.isOfType = host

            # Ram and CPU
            ram = self.onto.Ram()
            ram.withAllocatableValue = node["status"]["allocatable"]["memory"]
            ram.withCapacityValue = node["status"]["capacity"]["memory"]
            cpu = self.onto.CPU()
            cpu.withAllocatableValue = node["status"]["allocatable"]["cpu"]
            cpu.withCapacityValue = node["status"]["capacity"]["cpu"]
            nd.hasRawComputationalResource = [ram, cpu]

            if "topology.kubernetes.io/zone" in node["metadata"]["labels"].keys():
                nd.isLocated = node["metadata"]["labels"]["topology.kubernetes.io/zone"]
            else:
                nd.isLocated = "Node label not provided."
        ct.consistsOfNodes = nd_list
