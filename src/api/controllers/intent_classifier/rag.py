import faiss
import pandas as pd
from sentence_transformers import SentenceTransformer

# Load the CSV files with the correct encoding

metrics_df = pd.read_csv("/Users/shridhi/Downloads/metrics_metadata.csv", encoding='latin1')
applications_df = pd.read_csv("/Users/shridhi/Downloads/app_data.csv", encoding='latin1')

# Load the CSV files
metrics_df = pd.read_csv("/Users/shridhi/Downloads/metrics_metadata.csv", encoding='latin1')
applications_df = pd.read_csv("/Users/shridhi/Downloads/app_data.csv", encoding='latin1')

# Rename the relevant columns to 'Text'
metrics_df.rename(columns={'Definition': 'Text'}, inplace=True)
applications_df.rename(columns={'Description': 'Text'}, inplace=True)

# Concatenate the DataFrames
combined_df = pd.concat([applications_df, metrics_df], ignore_index=True, sort=False)

# Save the merged file
combined_df.to_csv("/Users/shridhi/Downloads/combined_data.csv", index=False)

# Verify the combined DataFrame
print("Combined DataFrame Columns:", combined_df.columns)
print(combined_df.info())
print(combined_df.head())

# Generate embeddings

# Initialize the Sentence Transformer model
model = SentenceTransformer('all-MiniLM-L6-v2')  # Lightweight and efficient model

# Generate embeddings for the text column
texts = combined_df['Text'].tolist()  # Now 'Text' column exists
embeddings = model.encode(texts, show_progress_bar=True)

print("This is embeddings:", embeddings)

# Use FAISS to index and search the embeddings for similar texts.
# Group similar texts using clustering algorithms like K-Means.