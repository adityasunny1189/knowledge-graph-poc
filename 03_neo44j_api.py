import requests
from neo4j import GraphDatabase

# Connect to Neo4j
uri = "bolt://localhost:7687"  # Update with your Neo4j instance URI
user = "neo4j"                 # Default username
password = "sprintoai"         # Replace with your password
driver = GraphDatabase.driver(uri, auth=(user, password))

# DBLP API endpoint
BASE_URL = "https://dblp.org/search/publ/api"

def add_relationship(tx, person1, person2, relationship, properties=None):
    query = f"""
    MERGE (a:Scientist {{name: $person1}})
    MERGE (b:Scientist {{name: $person2}})
    MERGE (a)-[r:{relationship}]->(b)
    SET r += $properties
    """
    tx.run(query, person1=person1, person2=person2, properties=properties or {})

def add_university(tx, scientist_name, university_name):
    # Create University node and connect the Scientist to it
    query = """
    MERGE (s:Scientist {name: $scientist_name})
    MERGE (u:University {name: $university_name})
    MERGE (s)-[:BELONGS_TO]->(u)
    """
    tx.run(query, scientist_name=scientist_name, university_name=university_name)

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

def add_coauthors_to_neo4j(scientist_name, coauthors, university_name=None):
    with driver.session() as session:
        # Add the scientist to the university node if university is known
        if university_name:
            session.execute_write(add_university, scientist_name, university_name)

        for coauthor in coauthors:
            session.execute_write(add_relationship, scientist_name, coauthor, "COAUTHOR")

def find_coauthors_same_university(tx, scientist_name):
    query = """
    MATCH (s:Scientist {name: $scientist_name})-[:COAUTHOR]-(coauthor)
    WHERE s.university IS NOT NULL AND coauthor.university = s.university
    RETURN coauthor.name AS coauthor_name
    """
    result = tx.run(query, scientist_name=scientist_name)
    return [record["coauthor_name"] for record in result]

def did_coauthor(tx, scientist1, scientist2):
    query = """
    MATCH (a:Scientist {name: $scientist1})-[:COAUTHOR]-(b:Scientist {name: $scientist2})
    RETURN COUNT(*) > 0 AS coauthored
    """
    result = tx.run(query, scientist1=scientist1, scientist2=scientist2)
    return result.single()["coauthored"]

if __name__ == "__main__":
    scientist = "Andrew Yao"
    university = "Princeton University"  # Example university
    coauthors = fetch_coauthor_data(scientist)
    add_coauthors_to_neo4j(scientist, coauthors, university)

    with driver.session() as session:
        print(f"Coauthors of {scientist} from the same university:")
        same_university_coauthors = session.execute_read(find_coauthors_same_university, scientist)
        print(same_university_coauthors)

        print(f"Did Andrew Yao and Yoshua Bengio coauthor a paper?")
        coauthored = session.execute_read(did_coauthor, "Andrew Yao", "Yoshua Bengio")
        print(coauthored)
