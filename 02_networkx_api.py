import requests
import pandas as pd
import networkx as nx

# DBLP API endpoint
BASE_URL = "https://dblp.org/search/publ/api"

G = nx.DiGraph()  # Use a directed graph for "student-of" relationships

def add_coauthors_to_graph(graph, scientist_name, coauthors):
    graph.add_node(scientist_name, type="scientist")  # Add the main scientist
    for coauthor in coauthors:
        graph.add_node(coauthor, type="scientist")
        graph.add_edge(scientist_name, coauthor, relationship="coauthor")
        graph.add_edge(coauthor, scientist_name, relationship="coauthor")  # Add both directions


def find_coauthors_same_university(graph, scientist_name):
    coauthors = [n for n, attr in graph[scientist_name].items() if attr["relationship"] == "coauthor"]
    # Example assumes university data is stored in node attributes (to be added in Step 4)
    same_university = [
        coauthor for coauthor in coauthors
        if graph.nodes[coauthor].get("university") == graph.nodes[scientist_name].get("university")
    ]
    return same_university


def did_coauthor(graph, scientist1, scientist2):
    return graph.has_edge(scientist1, scientist2) and graph[scientist1][scientist2]["relationship"] == "coauthor"


def fetch_coauthor_data(scientist_name):
    params = {
        "q": scientist_name,
        "h": 1000,  # Max results
        "format": "json"
    }
    response = requests.get(BASE_URL, params=params)
    data = response.json()
    coauthors = set()

    for hit in data.get("result", {}).get("hits", {}).get("hit", []):
        try:
            authors = hit.get("info", {}).get("authors", {}).get("author", [])
            # Ensure authors is always a list
            if isinstance(authors, dict):
                authors = [authors]
            elif isinstance(authors, str):
                authors = [authors]
            author_names = [a.get("text", "") for a in authors if isinstance(a, dict)]
            if scientist_name in author_names:
                coauthors.update(author_names)
        except KeyError as e:
            print(f"KeyError: {e} in record {hit}")
            continue
    coauthors.discard(scientist_name)  # Remove self
    return list(coauthors)


if __name__ == "__main__":
    scientist = "Andrew Yao"
    coauthors = fetch_coauthor_data(scientist)
    add_coauthors_to_graph(G, scientist, coauthors)
    
    print(f"Coauthors of {scientist} from the same university:")
    print(find_coauthors_same_university(G, scientist))
    
    print(f"Did Andrew Yao and Yoshua Bengio coauthor a paper?")
    print(did_coauthor(G, "Andrew Yao", "Yoshua Bengio"))



