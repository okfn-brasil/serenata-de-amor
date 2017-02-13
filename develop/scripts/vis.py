from IPython.display import IFrame
import json
import uuid
import os


def vis_network(nodes, edges, physics=False, graph_name=None):
    html = """
    <html>
    <head>
      <script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/vis/4.8.2/vis.min.js"></script>
      <link href="https://cdnjs.cloudflare.com/ajax/libs/vis/4.8.2/vis.min.js" rel="stylesheet" type="text/css">
    </head>
    <body>

    <div id="{id}"></div>

    <script type="text/javascript">
      var nodes = {nodes};
      var edges = {edges};

      var container = document.getElementById("{id}");

      var data = {{
        nodes: nodes,
        edges: edges
      }};

      var options = {{
          nodes: {{
              shape: 'dot',
              size: 25,
              font: {{
                  size: 14
              }}
          }},
          edges: {{
              font: {{
                  size: 14,
                  align: 'middle'
              }},
              color: 'gray',
              arrows: {{
                  to: {{enabled: true, scaleFactor: 0.5}}
              }},
              smooth: {{enabled: false}}
          }},
          physics: {{
              enabled: {physics}
          }}
      }};

      var network = new vis.Network(container, data, options);

    </script>
    </body>
    </html>
    """

    unique_id = str(uuid.uuid4())
    if graph_name:
        unique_id = graph_name

    html = html.format(id=unique_id, nodes=json.dumps(nodes), edges=json.dumps(edges), physics=json.dumps(physics))

    if not os.path.exists("figure"):
        os.makedirs("figure")
    filename = "figure/graph-{}.html".format(unique_id)

    file = open(filename, "w")
    file.write(html)
    file.close()

    return IFrame(filename, width="100%", height="400")

def draw(graph, options, physics=False, limit=100, graph_name=None):
    # The options argument should be a dictionary of node labels and property keys; it determines which property
    # is displayed for the node label. For example, in the movie graph, options = {"Movie": "title", "Person": "name"}.
    # Omitting a node label from the options dict will leave the node unlabeled in the visualization.
    # Setting physics = True makes the nodes bounce around when you touch them!
    query = """
    MATCH (n)
    WITH n, rand() AS random
    ORDER BY random
    LIMIT {limit}
    OPTIONAL MATCH (n)-[r]->(m)
    RETURN n AS source_node,
           id(n) AS source_id,
           r,
           m AS target_node,
           id(m) AS target_id
    """

    data = graph.run(query, limit=limit)

    nodes = []
    edges = []

    def get_vis_info(node, id):
        node_label = list(node.labels())[0]
        prop_key = options.get(node_label)
        vis_label = node.properties.get(prop_key, "")

        return {"id": id, "label": vis_label, "group": node_label, "title": repr(node.properties)}

    for row in data:
        source_node = row[0]
        source_id = row[1]
        rel = row[2]
        target_node = row[3]
        target_id = row[4]

        source_info = get_vis_info(source_node, source_id)

        if source_info not in nodes:
            nodes.append(source_info)

        if rel is not None:
            target_info = get_vis_info(target_node, target_id)

            if target_info not in nodes:
                nodes.append(target_info)

            edges.append({"from": source_info["id"], "to": target_info["id"], "label": rel.type()})

    return vis_network(nodes, edges, physics=physics, graph_name=graph_name)
