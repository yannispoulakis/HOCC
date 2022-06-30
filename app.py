from flask import Flask, request, render_template, Response
import json
import os
import requests
import uuid
import csv
from kubemantics.semantics_transformer import kube2onto
from kubemantics.utils import prepare_resources
from kubemantics.rules import semantic_rules
from kubemantics.kubeapi import kubeapi_conn

global cluster_id
cluster_id = str(uuid.uuid1())


# Main body that is executed outside of flask
def extraction_routine():

    conn = kubeapi_conn()

    k = kube2onto(cluster_id=cluster_id)

    # Retrieve ontology and transform kubernetes api output
    k.nodes_to_individuals(conn.get_nodes())
    # Rules.
    sr = semantic_rules(k.onto)
    sr.locality_rule()

    # save ontology with individuals
    k.onto.save(str(k.cluster_id), format="ntriples")

    prepare_resources(str(k.cluster_id), list(k.onto.individuals()), format="nt")

    response = requests.post(url=os.getenv("SEMANTICS-BLOCK-URL") + "/clusters", json=json.dumps(open(cluster_id+ "_indiviudals.json").read()))

    print(response)
    return response


app = Flask(__name__)


@app.route("/", methods=["GET"])
def render_home():
    """Home page"""
    return render_template("/main/home.html")


@app.route("/ontology-raw", methods=['GET', 'POST'])
def onto_raw():
    """Raw XML formatted ontology"""
    with open("/app/resource_ontology.owl", "r", encoding="utf8") as f:
        data = f.read()
    return Response(data, mimetype="text/xml")


@app.route("/nodes")
def render_nodes():
    conn = kubeapi_conn()
    return conn.get_nodes()


@app.route("/cluster-semantics")
def info2semantics():
    print("Kubemantics testing starts..............", flush=True)
    print("Workdir is : {}".format(os.getcwd()), flush=True)

    conn = kubeapi_conn()
    if len(conn.get_nodes()) > 0:
        print("Nodes Successfully retrieved")

    k = kube2onto(onto_path="/app/resource_ontology.owl", cluster_id=cluster_id)
    # Retrieve ontology and transform kubernetes api output
    k.nodes_to_individuals(conn.get_nodes())

    # Rules.
    sr = semantic_rules(k.onto)
    sr.locality_rule()

    if len(list(k.onto.individuals())) > 0 :
        print("Individuals created", flush=True)
    
    import csv

    with open("test.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow(["asdasd", "asdasd"])

    with open("test.csv", "r") as f:
        reader = csv.reader(f)
        for row in reader:
            print(', '.join(row), flush=True)
            
    k.onto.save("/app/" + str(k.cluster_id), format="ntriples")
    
    if os.path.exists(str(k.cluster_id)):
        print("Ontology with individuals saved....", flush=True)

    print("CWD files: {}".format(os.listdir(os.getcwd())), flush=True)


    prepare_resources("/app/" + str(k.cluster_id), list(k.onto.individuals()), format="nt")

    return Response(open("/app/" + str(k.cluster_id) + "__individuals.json").read(), mimetype="text/json")


@app.route("/post-cluster-semantics")
def semantics2ie():
    response = requests.post(url=os.getenv("SEMANTICS-BLOCK-URL") + "/clusters",
                             json=json.dumps(open("/app/" + cluster_id + "_indiviudals.json").read()))

    print(response)
    return response


@app.route("/annotate-cluster", methods=['GET', 'POST'])
def annotate_cluster():
    """Registers a new cluster. The input body should consist of three different jsons"""

    if request.method == "GET":
        return render_template('/main/resource_registration_visual.html')

        return "200"


@app.route("/local-testing")
def local_test_node2semantics():
    """Tests locally if the describe nodes output is converted sucessfully to semantics. """

    # Retrieve describe nodes output
    node_list = json.loads(open("input examples/nodes.json", "r").read())

    # Retrieve ontology and transform kubernetes api output
    k = kube2onto(onto_path="resource_ontology.owl")
    k.nodes_to_individuals(node_list)

    # Rules.
    sr = semantic_rules(k.onto)
    sr.locality_rule()
    ct = [x for x in k.onto.individuals() if x.is_a[0].__name__ =="Cluster"][0]
    print(ct)
    print(ct.hasLocality)
    k.onto.save(str(k.cluster_id), format="ntriples")

    data = open(str(k.cluster_id), encoding="utf8").read()

    prepare_resources(str(k.cluster_id), list(k.onto.individuals()), format="nt")
    return Response(data, mimetype="text/xml")


if __name__ == "__main__":
    #extraction_routine()
    app.run("0.0.0.0", 5000, debug=False)
