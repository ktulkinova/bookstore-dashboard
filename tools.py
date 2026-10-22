import json
import pandas as pd



def load(store, table):
    return pd.read_parquet(f'clean/{store}/{table}.parquet')


def get_summary(store: str) -> dict:
    """Main results of a store: top 5 days by revenue, number of unique users,
    number of unique author sets, most popular authors, best buyer ids.

    Args:
        store: STORE1, STORE2, STORE3, STORE4 or STORE5
    """
    with open(f'results/{store}.json') as f:
        return json.load(f)


def get_revenue(store: str, date_from: str, date_to: str) -> dict:
    """Revenue in USD, number of orders, sold books and average order value in USD
    for a period (both dates included). For one day use the same date twice.

    Args:
        store: STORE1, STORE2, STORE3, STORE4 or STORE5
        date_from: first date, YYYY-MM-DD
        date_to: last date, YYYY-MM-DD
    """
    orders = load(store, 'orders')
    period = orders[(orders['date'] >= date_from) & (orders['date'] <= date_to)]
    return {
        'revenue_usd': round(float(period['paid_price'].sum()), 2),
        'orders': len(period),
        'books_sold': int(period['quantity'].sum()),
        'average_order_usd': round(float(period['paid_price'].mean()), 2) if len(period) > 0 else 0,
    }


def get_monthly_revenue(store: str) -> dict:
    """Revenue in USD for every month (YYYY-MM).

    Args:
        store: STORE1, STORE2, STORE3, STORE4 or STORE5
    """
    orders = load(store, 'orders')
    month = orders['date'].dt.strftime('%Y-%m')
    revenue = orders.groupby(month)['paid_price'].sum().round(2)
    return revenue.to_dict()


def get_top_days(store: str, n: int) -> dict:
    """Days with the highest revenue (date -> revenue in USD).

    Args:
        store: STORE1, STORE2, STORE3, STORE4 or STORE5
        n: how many days
    """
    orders = load(store, 'orders')
    daily = orders.groupby(orders['date'].dt.strftime('%Y-%m-%d'))['paid_price'].sum().round(2)
    return daily.sort_values(ascending=False).head(n).to_dict()


def get_top_authors(store: str, n: int) -> dict:
    """Authors (or author sets) with the most sold books (authors -> books sold).

    Args:
        store: STORE1, STORE2, STORE3, STORE4 or STORE5
        n: how many authors
    """
    orders = load(store, 'orders')
    books = load(store, 'books')
    sold = orders.merge(books, left_on='book_id', right_on='id')
    by_author = sold.groupby('authors')['quantity'].sum()
    return by_author.sort_values(ascending=False).head(n).to_dict()


def find_author(store: str, name: str) -> dict:
    """Find authors by name (or part of the name) and count their sold books.
    Returns the total for all found books and books sold for every author set
    (a book can have several authors).

    Args:
        store: STORE1, STORE2, STORE3, STORE4 or STORE5
        name: author name or part of the name, not case sensitive
    """
    orders = load(store, 'orders')
    books = load(store, 'books')
    sold = orders.merge(books, left_on='book_id', right_on='id')
    sold = sold[sold['authors'].str.contains(name, case=False, regex=False)]
    by_author = sold.groupby('authors')['quantity'].sum().sort_values(ascending=False)
    return {'books_sold_total': int(sold['quantity'].sum()), 'by_author_set': by_author.head(10).to_dict()}


def get_top_books(store: str, n: int) -> dict:
    """Book titles with the most sold copies (title -> copies sold).

    Args:
        store: STORE1, STORE2, STORE3, STORE4 or STORE5
        n: how many books
    """
    orders = load(store, 'orders')
    books = load(store, 'books')
    sold = orders.merge(books, left_on='book_id', right_on='id')
    by_title = sold.groupby('title')['quantity'].sum()
    return by_title.sort_values(ascending=False).head(n).to_dict()


def get_biggest_orders(store: str, n: int) -> list:
    """The most expensive orders, sorted from the biggest. For every order returns
    order id, user id, date, book title, quantity and paid price in USD.

    Args:
        store: STORE1, STORE2, STORE3, STORE4 or STORE5
        n: how many orders
    """
    orders = load(store, 'orders')
    books = load(store, 'books')
    biggest = orders.sort_values('paid_price', ascending=False).head(n)
    titles = books.set_index('id')['title']

    result = []
    for _, row in biggest.iterrows():
        result.append({
            'order_id': int(row['id']),
            'user_id': int(row['user_id']),
            'date': row['date'].strftime('%Y-%m-%d'),
            'title': str(titles[row['book_id']]),
            'quantity': int(row['quantity']),
            'paid_price_usd': round(float(row['paid_price']), 2),
        })
    return result


def get_revenue_by_genre(store: str) -> dict:
    """Revenue in USD for every book genre, sorted from the biggest.

    Args:
        store: STORE1, STORE2, STORE3, STORE4 or STORE5
    """
    orders = load(store, 'orders')
    books = load(store, 'books')
    sold = orders.merge(books, left_on='book_id', right_on='id')
    by_genre = sold.groupby('genre')['paid_price'].sum().round(2)
    return by_genre.sort_values(ascending=False).to_dict()


def find_customer(store: str, name: str) -> list:
    """Find customers by name (or part of the name). For every found person returns
    all names and all user ids (the same person can have several ids) and total spending in USD.

    Args:
        store: STORE1, STORE2, STORE3, STORE4 or STORE5
        name: name or part of the name, not case sensitive
    """
    users = load(store, 'users')
    orders = load(store, 'orders')
    found = users[users['name'].str.contains(name, case=False, regex=False)]

    result = []
    for person in found['person'].unique()[:10]:
        ids = users.loc[users['person'] == person, 'id'].tolist()
        names = users.loc[users['person'] == person, 'name'].unique().tolist()
        spent = orders.loc[orders['user_id'].isin(ids), 'paid_price'].sum()
        result.append({'names': names, 'user_ids': ids, 'spent_usd': round(float(spent), 2)})
    return result


def get_top_customers(store: str, n: int) -> list:
    """Customers who spent the most money. Every customer is a real person with all his user ids.

    Args:
        store: STORE1, STORE2, STORE3, STORE4 or STORE5
        n: how many customers
    """
    users = load(store, 'users')
    orders = load(store, 'orders')
    orders['person'] = orders['user_id'].map(users.set_index('id')['person'])
    spent = orders.groupby('person')['paid_price'].sum().sort_values(ascending=False).head(n)

    result = []
    for person, money in spent.items():
        ids = users.loc[users['person'] == person, 'id'].tolist()
        names = users.loc[users['person'] == person, 'name'].unique().tolist()
        result.append({'names': names, 'user_ids': ids, 'spent_usd': round(float(money), 2)})
    return result


def get_user(store: str, user_id: int) -> dict:
    """Information about one user id: the real person behind it (all names and all user ids),
    number of orders, books bought and total spending in USD.

    Args:
        store: STORE1, STORE2, STORE3, STORE4 or STORE5
        user_id: user id, for example 48403
    """
    users = load(store, 'users')
    orders = load(store, 'orders')
    found = users[users['id'] == user_id]
    if len(found) == 0:
        return {'error': f'user {user_id} not found in {store}'}

    person = users[users['person'] == found['person'].iloc[0]]
    ids = person['id'].tolist()
    bought = orders[orders['user_id'].isin(ids)]
    return {
        'names': person['name'].unique().tolist(),
        'user_ids': ids,
        'orders': len(bought),
        'books_bought': int(bought['quantity'].sum()),
        'spent_usd': round(float(bought['paid_price'].sum()), 2),
    }


def compare_stores() -> dict:
    """Total revenue in USD and number of orders for every store."""
    result = {}
    for i in range(1, 6):
        store = f'STORE{i}'
        orders = load(store, 'orders')
        result[store] = {'revenue_usd': round(float(orders['paid_price'].sum()), 2), 'orders': len(orders)}
    return result


ALL_TOOLS = [get_summary, get_revenue, get_monthly_revenue, get_top_days, get_top_authors, find_author,
             get_top_books, get_biggest_orders, get_revenue_by_genre, find_customer, get_top_customers, get_user, compare_stores]
