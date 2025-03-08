import json
from typing import List
import pandas as pd
from langchain.schema import Document

def load_documents(file_loc: str) -> List[Document]:
    file_path = file_loc + "/Final_client_data.csv"
    df = pd.read_csv(file_path)
    documents = []
    
    for _, row in df.iterrows():
        try:
            metadata = json.loads(row["Metadata"]) if pd.notna(row["Metadata"]) else {}
        except json.JSONDecodeError:
            metadata = {}
        
        document = Document(
            page_content=row["Description"],  # Use "Description" as the main text content
            metadata={
                **metadata,
                "Name": row["Name"],
                "Metrics": row["Metrics"],
                "Type": row["Type"]
            }
        )
        documents.append(document)

    return documents