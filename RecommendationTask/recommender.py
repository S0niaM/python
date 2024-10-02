import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

data = pd.read_csv('simulated_user_item_data.csv') 

# NOTE - IF NOT ABLE TO FIND DATA FILE PLEASE RUN (data.py)

user_item_matrix = data.pivot(index='user_id', columns='item_id', values='rating')

# Calculate item similarity using cosine similarity
item_similarity = cosine_similarity(user_item_matrix.T)

def get_recommendations(user_id, top_n=10):
    user_ratings = user_item_matrix.loc[user_id]
    user_ratings = user_ratings[pd.notnull(user_ratings)]

    item_similarity_scores = item_similarity[user_ratings.index]
    item_similarity_scores = item_similarity_scores.dot(user_ratings) / np.sqrt(np.sum(user_ratings**2))

    item_similarity_scores = item_similarity_scores.sort_values(ascending=False)

    return item_similarity_scores.head(top_n)

# Get recommendations for a specific user
recommended_items = get_recommendations(user_id=123, top_n=5)
print(recommended_items)