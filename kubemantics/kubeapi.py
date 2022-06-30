from kubernetes import client, config
import json


class kubeapi_conn:
    def __init__(self):
        config.load_incluster_config()
        self.client = client.CoreV1Api()
        self.node_list = ""

    def get_nodes(self):
        self.node_list = self.client.list_node(_preload_content=False)
        self.node_list = json.loads(self.node_list.data)
        return self.node_list
