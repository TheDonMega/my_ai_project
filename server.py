# A simple example for your future server.py
import os

def load_knowledge_base():
    knowledge = []
    folder_path = "./knowledge_base"
    for filename in os.listdir(folder_path):
        if filename.endswith(".md"):
            with open(os.path.join(folder_path, filename), 'r') as f:
                content = f.read()
                knowledge.append({"filename": filename, "content": content})
    return knowledge

# The AI agent would then get data from this function
all_my_data = load_knowledge_base()
print(f"Loaded {len(all_my_data)} documents.")
