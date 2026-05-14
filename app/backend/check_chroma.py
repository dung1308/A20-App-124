import chromadb
import os

# Define the path to your chroma database
CHROMA_PATH = r"app\backend\chroma_db"

def inspect_chroma_metadata():
    if not os.path.exists(CHROMA_PATH):
        print(f"Error: Path {CHROMA_PATH} does not exist.")
        return

    # Initialize the client
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    
    # List all collections to see what we have
    collections = client.list_collections()
    if not collections:
        print("No collections found in the database.")
        return

    for collection_info in collections:
        collection_name = collection_info.name
        print(f"\n--- Checking Collection: {collection_name} ---")
        
        collection = client.get_collection(name=collection_name)
        
        # Peek at the first few items
        results = collection.peek(limit=5)
        
        metadatas = results.get('metadatas', [])
        
        if not metadatas or metadatas[0] is None:
            print(f"No metadata found in collection '{collection_name}'.")
            continue

        # Check for specific keys
        found_keys = metadatas[0].keys()
        target_keys = ['url', 'link', 'date_published', 'date_crawled', 'retrieved_date', 'source']
        
        print(f"Available metadata keys: {list(found_keys)}")
        
        for key in target_keys:
            if key in found_keys:
                print(f"[FOUND] {key}: {metadatas[0][key]}")
            else:
                print(f"[MISSING] {key}")

if __name__ == "__main__":
    inspect_chroma_metadata()
