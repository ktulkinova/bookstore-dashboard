import json
import os
import matplotlib.pyplot as plt
import pandas as pd



def find_people(users):
    users['person'] = users['id']
    keys = [
        ['name', 'address', 'phone'],
        ['name', 'address', 'email'],
        ['name', 'phone', 'email'],
        ['address', 'phone', 'email'],
    ]
    changed = True
    while changed:
        before = users['person'].copy()
        for key in keys:
            smallest = users.groupby(key)['person'].transform('min')
            users['person'] = smallest.fillna(users['person']).astype(int)
        changed = not users['person'].equals(before)

    return users


def author_set(author):
    names = [name.strip() for name in author.split(',')]
    return ', '.join(sorted(names))


os.makedirs('results', exist_ok=True)

for i in range(1, 6):
    store = f'STORE{i}'
    users = pd.read_parquet(f'clean/{store}/users.parquet')
    books = pd.read_parquet(f'clean/{store}/books.parquet')
    orders = pd.read_parquet(f'clean/{store}/orders.parquet')

    # top 5 days by revenue
    daily = orders.groupby('date')['paid_price'].sum().round(2)
    # days without orders get 0, otherwise the chart draws a line over the gap
    daily = daily.asfreq('D', fill_value=0)
    daily.to_csv(f'results/{store}_daily.csv')
    top5 = daily.sort_values(ascending=False).head(5)
    top5_days = top5.index.strftime('%Y-%m-%d').tolist()

    # unique users
    users = find_people(users)
    unique_users = users['person'].nunique()
    users.to_parquet(f'clean/{store}/users.parquet', index=False)

    # unique sets of authors
    books['authors'] = books['author'].apply(author_set)
    unique_authors = books['authors'].nunique()
    books.to_parquet(f'clean/{store}/books.parquet', index=False)

    # most popular authors
    sold = orders.merge(books[['id', 'authors']], left_on='book_id', right_on='id')
    by_author = sold.groupby('authors')['quantity'].sum()
    top_authors = by_author[by_author == by_author.max()].index.tolist()

    # best buyer with all ids
    orders['person'] = orders['user_id'].map(users.set_index('id')['person'])
    spent = orders.groupby('person')['paid_price'].sum()
    best = spent.idxmax()
    best_ids = sorted(users.loc[users['person'] == best, 'id'].tolist())

    # daily revenue chart
    plt.figure(figsize=(12, 4))
    plt.plot(daily.index, daily.values)
    plt.title(f'{store} daily revenue')
    plt.ylabel('USD')
    plt.savefig(f'results/{store}_revenue.png')
    plt.close()

    result = {
        'top5_days': top5_days,
        'unique_users': int(unique_users),
        'unique_author_sets': int(unique_authors),
        'top_authors': top_authors,
        'best_buyer': [int(x) for x in best_ids],
    }
    with open(f'results/{store}.json', 'w') as f:
        json.dump(result, f, indent=2)

    print(store, result)
