import json
import pandas as pd

import streamlit as st

import chat

st.set_page_config(page_title='Book Stores Dashboard', layout='wide')

stores = ['STORE1', 'STORE2', 'STORE3', 'STORE4', 'STORE5']


def show_store(store):
    with open(f'results/{store}.json') as f:
        result = json.load(f)
    daily = pd.read_csv(f'results/{store}_daily.csv', index_col='date', parse_dates=True)

    st.caption(f"Data from {daily.index.min():%Y-%m-%d} to {daily.index.max():%Y-%m-%d}")

    col1, col2, col3 = st.columns(3)
    col1.metric('Total revenue', f"${daily['paid_price'].sum():,.2f}", border=True)
    col2.metric('Unique users', result['unique_users'], border=True)
    col3.metric('Unique author sets', result['unique_author_sets'], border=True)

    left, right = st.columns(2)
    with left:
        st.subheader('Top 5 days by revenue')
        top5 = daily.loc[result['top5_days']].reset_index()
        top5['date'] = top5['date'].dt.strftime('%Y-%m-%d')
        top5.columns = ['Date', 'Revenue, $']
        st.dataframe(top5, hide_index=True, width='stretch')

    with right:
        st.subheader('Most popular author(s)')
        for authors in result['top_authors']:
            st.info(authors)

        st.subheader('Best buyer ids')
        st.code(str(result['best_buyer']))

    st.subheader('Daily revenue')
    st.line_chart(daily['paid_price'], y_label='USD')


st.title('Book Stores Dashboard')

tabs = st.tabs(stores + ['AI chat'])

for i in range(len(stores)):
    with tabs[i]:
        show_store(stores[i])

with tabs[-1]:
    try:
        api_key = st.secrets['GEMINI_API_KEY']
    except Exception:
        st.warning('Gemini API key is missing. Add GEMINI_API_KEY to .streamlit/secrets.toml')
        st.stop()

    store = st.selectbox('Store for questions (if the question does not say it)', ['All stores'] + stores)

    if 'client' not in st.session_state:
        st.session_state.client = chat.new_client(api_key)

    if st.session_state.get('chat_store') != store:
        st.session_state.chat = chat.new_chat(st.session_state.client, store)
        st.session_state.chat_store = store
        st.session_state.messages = []

    for role, text in st.session_state.messages:
        st.chat_message(role).write(text)

    question = st.chat_input('Ask about the data, e.g. "What was the revenue in March 2026?"')
    if question:
        st.chat_message('user').write(question)
        try:
            with st.spinner('Thinking...'):
                answer = chat.ask(st.session_state.chat, question)
            answer = answer.replace('$', '\\$')
        except Exception as error:
            if '429' in str(error):
                answer = 'Too many questions, Gemini limit is reached. Please wait a minute and try again.'
            else:
                answer = f'Error: {error}'
        st.chat_message('assistant').write(answer)
        st.session_state.messages.append(('user', question))
        st.session_state.messages.append(('assistant', answer))
