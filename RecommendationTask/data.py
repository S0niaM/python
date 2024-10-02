import pandas as pd
import numpy as np


num_users = 1000
num_items = 500


user_ids = np.random.randint(1, num_users + 1, size=10000)
item_ids = np.random.randint(1, num_items + 1, size=10000)


ratings = np.random.randint(1, 6, size=10000)


data = {'user_id': user_ids, 'item_id': item_ids, 'rating': ratings}
df = pd.DataFrame(data)


df.to_csv('simulated_user_item_data.csv', index=False)