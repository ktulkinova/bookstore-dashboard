import os
import pandas as pd
import yaml

euro_to_usd = 1.2


def clean_users(users):
    
    users = users.drop_duplicates()
    for col in ['name', 'address', 'phone', 'email']:
        users[col] = users[col].astype('string').str.strip().replace('', pd.NA)

    users['phone'] = users['phone'].str.replace(r'[().\s-]', '', regex=True)
    return users



def clean_books(books):
    books = books.drop_duplicates()
    books['publisher'] = books['publisher'].astype('string').str.strip().replace(['', 'NULL', '-'], pd.NA)

    books['year'] = pd.to_numeric(books['year'], errors='coerce')
    books['year'] = books['year'].where(books['year'] > 0).astype('Int64')
    return books



def get_price(price):
    is_euro = price.str.contains('€|EUR')

    price = price.str.replace(r'(\d+)[$€¢](\d+)', r'\1.\2', regex=True)
    price = price.str.replace(r'[^\d.]', '', regex=True).astype(float)

    price[is_euro] = price[is_euro] * euro_to_usd
    return price.round(2)


def get_date(timestamp):
    formats = [
        (r'(\d{4}-\d{2}-\d{2})', '%Y-%m-%d'),
        (r'(\d{2}/\d{2}/\d{2})', '%m/%d/%y'),
        (r'(\d{1,2}\.\d{1,2}\.\d{4})', '%d.%m.%Y'),
        (r'(\d{1,2}-[A-Za-z]{3}-\d{4})', '%d-%b-%Y'),
        (r'(\d{1,2}-[A-Za-z]{4,}-\d{4})', '%d-%B-%Y'),
        (r'([A-Za-z]{3} +\d{1,2} .* \d{4})', '%b %d %H:%M:%S %Y'),
    ]

    date = pd.Series(pd.NaT, index=timestamp.index)
    for pattern, date_format in formats:
        part = timestamp.str.extract(pattern)[0]
        date = date.fillna(pd.to_datetime(part, format=date_format, errors='coerce'))
    return date.dt.normalize()


def clean_orders(orders):
    orders = orders.drop_duplicates()
    orders['shipping'] = orders['shipping'].astype('string').str.strip().replace(['', 'NULL'], pd.NA)

    orders['unit_price'] = get_price(orders['unit_price'])
    orders['paid_price'] = (orders['quantity'] * orders['unit_price']).round(2)

    orders['date'] = get_date(orders['timestamp'])
    orders['year'] = orders['date'].dt.year
    orders['month'] = orders['date'].dt.month
    orders['day'] = orders['date'].dt.day

    print('orders without date:', orders['date'].isna().sum(), 'without price:', orders['paid_price'].isna().sum())
    return orders


for i in range(1, 6):
    store = f'STORE{i}'
    print(store)

    users = pd.read_csv(f'data/{store}/users.csv')
    orders = pd.read_parquet(f'data/{store}/orders.parquet')
    with open(f'data/{store}/books.yaml') as f:
        books = pd.DataFrame(yaml.safe_load(f))
    books.columns = books.columns.str.lstrip(':')

    os.makedirs(f'clean/{store}', exist_ok=True)
    clean_users(users).to_parquet(f'clean/{store}/users.parquet', index=False)
    clean_books(books).to_parquet(f'clean/{store}/books.parquet', index=False)
    clean_orders(orders).to_parquet(f'clean/{store}/orders.parquet', index=False)
