from flask import Flask, render_template, redirect, url_for, jsonify, session, request, send_from_directory
from flask_paginate import Pagination, get_page_args
import mysqlDB as msq
import secrets
from datetime import datetime, timedelta
# from googletrans import Translator
import random
from flask_session import Session
import redis
from bin.config_utils import SESSION_FLASK_KEY, MISTRAL_API_KEY
from bin.wrapper_mistral import MistralChatManager
from markupsafe import Markup
import json
import logging
import requests

app = Flask(__name__)

# Klucz tajny do szyfrowania sesji
app.config['SECRET_KEY'] = SESSION_FLASK_KEY

# Ustawienia dla Flask-Session
app.config['SESSION_TYPE'] = 'redis'  # Redis jako magazyn sesji
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10)
app.config['SESSION_KEY_PREFIX'] = 'session:'  # Prefiks dla kluczy w Redis
app.config['SESSION_REDIS'] = redis.StrictRedis(host='localhost', port=6379, db=0)

# app.config['SECRET_KEY'] = secrets.token_hex(16)
# app.config['SESSION_TYPE'] = 'filesystem'  # Możesz wybrać inny backend, np. 'redis', 'sqlalchemy', itp.

# stronicowanie
app.config['PER_PAGE'] = 6

Session(app)

# translator = Translator()

def getLangText(text, dest="en", source="pl"):

    if not text:
        return text
   
    # bezpiecznik: nie tłumacz "ścian"
    if len(text) > 4000:
        return text
    try:
        r = requests.post(
            "http://127.0.0.1:5055/translate",
            json={"text": text, "source": source, "target": dest, "format": "text"},
            timeout=(2, 8),
        )
        r.raise_for_status()
        print(r.json().get("translated", text))
        return r.json().get("translated", text)
    except Exception as e:
        print(f"Exception Error: {e}")
        return text



def getLangText_old2(text, dest='en'):
    if not text:  # Sprawdza, czy text jest pusty lub None
        return ""

    try:
        mgr = MistralChatManager(MISTRAL_API_KEY)
        out = mgr.translate(text, target_lang='en')
        if out:
            return out
        # translation = translator.translate(str(text), dest=dest)
        # if translation and translation.text:
        #     return translation.text
        else:
            return text  # Jeśli tłumaczenie zwróciło None, zwracamy oryginalny tekst
    except Exception as e:
        print(f"Error translating text: {text} - {e}")
        return text  # W razie błędu zwracamy oryginalny tekst

    
def getLangText_old(text):
    """Funkcja do tłumaczenia tekstu z polskiego na angielski"""
    # translator = Translator()
    # translation = translator.translate(str(text), dest='en')
    # return translation.text

def format_date(date_input, pl=True):
    ang_pol = {
        'January': 'styczeń', 'February': 'luty', 'March': 'marzec', 'April': 'kwiecień',
        'May': 'maj', 'June': 'czerwiec', 'July': 'lipiec', 'August': 'sierpień',
        'September': 'wrzesień', 'October': 'październik', 'November': 'listopad', 'December': 'grudzień'
    }

    if isinstance(date_input, str):
        # Usuwamy mikrosekundy, jeśli są
        date_input = date_input.split('.')[0]
        date_object = datetime.strptime(date_input, '%Y-%m-%d %H:%M:%S')
    else:
        date_object = date_input  # Jeśli to już datetime, używamy go bez zmian

    formatted_date = date_object.strftime('%d %B %Y')

    if pl:
        for en, pl in ang_pol.items():
            formatted_date = formatted_date.replace(en, pl)

    return formatted_date

def format_date_old(date_input, pl=True):
    ang_pol = {
        'January': 'styczeń',
        'February': 'luty',
        'March': 'marzec',
        'April': 'kwiecień',
        'May': 'maj',
        'June': 'czerwiec',
        'July': 'lipiec',
        'August': 'sierpień',
        'September': 'wrzesień',
        'October': 'październik',
        'November': 'listopad',
        'December': 'grudzień'
    }
    # Sprawdzenie czy data_input jest instancją stringa; jeśli nie, zakładamy, że to datetime
    if isinstance(date_input, str):
        date_object = datetime.strptime(date_input, '%Y-%m-%d %H:%M:%S')
    else:
        # Jeśli date_input jest już obiektem datetime, używamy go bezpośrednio
        date_object = date_input

    formatted_date = date_object.strftime('%d %B %Y')
    if pl:
        for en, pl in ang_pol.items():
            formatted_date = formatted_date.replace(en, pl)

    return formatted_date

#  Funkcja pobiera dane z bazy danych 
def take_data_where_ID(key, table, id_name, ID):
    dump_key = msq.connect_to_database(f'SELECT {key} FROM {table} WHERE {id_name} = {ID};')
    return dump_key

def take_data_where_ID_AND_somethig(key, table, id_name, ID, nameSomething, valSomething):
    if isinstance(ID, str):
        ID = f"'{ID}'"
    if isinstance(valSomething, str):
        valSomething = f"'{valSomething}'"
    dump_key = msq.connect_to_database(f'SELECT {key} FROM {table} WHERE {id_name} = {ID} AND {nameSomething} = {valSomething};')
    return dump_key

def take_data_where_ID_AND_somethig_AND_Something(key, table, id_name, ID, nameSomething, valSomething, nameSomethingOther, valSomethingOther):
    if isinstance(ID, str):
        ID = f"'{ID}'"
    if isinstance(valSomething, str):
        valSomething = f"'{valSomething}'"
    if isinstance(valSomethingOther, str):
        valSomethingOther = f"'{valSomethingOther}'"
    dump_key = msq.connect_to_database(f'SELECT {key} FROM {table} WHERE {id_name} = {ID} AND {nameSomething} = {valSomething} AND {nameSomethingOther} = {valSomethingOther};')
    return dump_key



def take_data_table(key, table):
    dump_key = msq.connect_to_database(f'SELECT {key} FROM {table};')
    return dump_key



def generator_teamDB(lang='pl'):
    took_teamD = take_data_table('*', 'workers_team')
    teamData = []
    for data in took_teamD:
        # dostosowane dla dmd budownictwo
        if data[4] == 'dmd budownictwo':
            theme = {
                'ID': int(data[0]),
                'EMPLOYEE_PHOTO': data[1],
                'EMPLOYEE_NAME': data[2],
                'EMPLOYEE_ROLE': data[3] if lang=='pl' else getLangText(data[3]),
                'EMPLOYEE_DEPARTMENT': data[4],
                'PHONE':'' if data[5] is None else data[5],
                'EMAIL': '' if data[6] is None else data[6],
                'FACEBOOK': '' if data[7] is None else data[7],
                'LINKEDIN': '' if data[8] is None else data[8],
                'DATE_TIME': data[9],
                'STATUS': int(data[10])
            }
            teamData.append(theme)
    return teamData

def generator_subsDataDB():
    subsData = []
    took_subsD = take_data_table('*', 'newsletter')
    for data in took_subsD:
        if data[4] != 1: continue
        ID = data[0]
        theme = {
            'id': ID, 
            'email':data[2],
            'name':data[1], 
            'status': str(data[4]), 
            }
        subsData.append(theme)
    return subsData

def generator_daneDBList(lang='pl'):
    limit = 'LIMIT 6' if lang != 'pl' else ''

    # Pobieramy wszystkie dane jednym zapytaniem
    query = f"""
        SELECT 
            bp.ID, 
            c.ID as content_id, 
            ANY_VALUE(c.TITLE) as TITLE, 
            ANY_VALUE(c.CONTENT_MAIN) as CONTENT_MAIN, 
            ANY_VALUE(c.HIGHLIGHTS) as HIGHLIGHTS, 
            ANY_VALUE(c.HEADER_FOTO) as HEADER_FOTO, 
            ANY_VALUE(c.CONTENT_FOTO) as CONTENT_FOTO, 
            ANY_VALUE(c.BULLETS) as BULLETS, 
            ANY_VALUE(c.TAGS) as TAGS, 
            ANY_VALUE(c.CATEGORY) as CATEGORY, 
            ANY_VALUE(c.DATE_TIME) as DATE_TIME,
            ANY_VALUE(a.NAME_AUTHOR) as NAME_AUTHOR, 
            ANY_VALUE(a.ABOUT_AUTHOR) as ABOUT_AUTHOR, 
            ANY_VALUE(a.AVATAR_AUTHOR) as AVATAR_AUTHOR, 
            ANY_VALUE(a.FACEBOOK) as FACEBOOK, 
            ANY_VALUE(a.TWITER_X) as TWITER_X, 
            ANY_VALUE(a.INSTAGRAM) as INSTAGRAM,
            COALESCE(
                GROUP_CONCAT(
                    JSON_OBJECT(
                        'id', cm.ID, 
                        'message', cm.COMMENT_CONNTENT,  
                        'user', nw.CLIENT_NAME, 
                        'e-mail', nw.CLIENT_EMAIL, 
                        'avatar', nw.AVATAR_USER,
                        'data-time', cm.DATE_TIME
                    )
                ), '[]'
            ) as comments
        FROM blog_posts bp
        JOIN contents c ON bp.CONTENT_ID = c.ID
        JOIN authors a ON bp.AUTHOR_ID = a.ID  
        LEFT JOIN comments cm ON cm.BLOG_POST_ID = bp.ID
        LEFT JOIN newsletter nw ON nw.ID = cm.AUTHOR_OF_COMMENT_ID
        GROUP BY bp.ID
        ORDER BY bp.ID DESC
        {limit};

    """

    all_posts = msq.connect_to_database(query)
    daneList = []
    for post in all_posts:
        (
            id, id_content, title, content_main, highlights, mainFoto, contentFoto, 
            bullets, tags, category, date_time, author, author_about, author_avatar, 
            author_facebook, author_twitter, author_instagram, comments_json
        ) = post

        # Parsowanie JSON z komentarzami (jeśli są)
        comments_dict = {}

        if comments_json and comments_json.strip():  # Sprawdzamy, czy nie jest pusty
            
            try:
                comments_list = json.loads(f'[{comments_json}]')  # Parsowanie JSON
                for i, comment in enumerate(comments_list):
                    if comment['message'] is not None and comment['user'] is not None:
                        comments_dict[i] = {
                            'id': comment['id'],
                            'message': comment['message'] if lang == 'pl' else getLangText(comment['message']),
                            'user': comment['user'],
                            'e-mail': comment['e-mail'],
                            'avatar': comment['avatar'],
                            'data-time': format_date(comment['data-time']) if comment['data-time'] else "Brak daty",
                        }

            except json.JSONDecodeError:
                comments_dict = {}  # Jeśli JSON jest błędny, ustaw pusty słownik


        # Przetwarzanie listy dodatkowej (bullets) i tagów
        bullets_list = str(bullets).split('#splx#') if lang == 'pl' else str(getLangText(bullets)).replace('#SPLX#', '#splx#').split('#splx#')
        tags_list = str(tags).split(', ') if lang == 'pl' else str(getLangText(tags)).split(', ')

        # Tłumaczenie pól jeśli trzeba
        if lang != 'pl':
            title = getLangText(title)
            content_main = getLangText(content_main)
            highlights = getLangText(highlights)
            category = getLangText(category)
            author_about = getLangText(author_about)
            date_time = format_date(date_time, False)
        else:
            date_time = format_date(date_time)

        theme = {
            'id': id_content,
            'title': title,
            'introduction': content_main,
            'highlight': highlights,
            'mainFoto': mainFoto,
            'contentFoto': contentFoto,
            'additionalList': bullets_list,
            'tags': tags_list,
            'category': category,
            'data': date_time,
            'author': author,
            'author_about': author_about,
            'author_avatar': author_avatar,
            'author_facebook': author_facebook,
            'author_twitter': author_twitter,
            'author_instagram': author_instagram,
            'comments': comments_dict
        }
        daneList.append(theme)
    
    return daneList


def generator_daneDBList_old(lang='pl'):
    limit = ''
    if lang!='pl':
        limit = 'LIMIT 5'
    daneList = []
    took_allPost = msq.connect_to_database(f'SELECT * FROM blog_posts ORDER BY ID DESC {limit};') # take_data_table('*', 'blog_posts')
    for post in took_allPost:
        id = post[0]
        id_content = post[1]
        id_author = post[2]

        allPostComments = take_data_where_ID('*', 'comments', 'BLOG_POST_ID', id)
        comments_dict = {}
        for i, com in enumerate(allPostComments):
            comments_dict[i] = {}
            comments_dict[i]['id'] = com[0]
            comments_dict[i]['message'] = com[2] if lang=='pl' else getLangText(com[2])
            comments_dict[i]['user'] = take_data_where_ID('CLIENT_NAME', 'newsletter', 'ID', com[3])[0][0]
            comments_dict[i]['e-mail'] = take_data_where_ID('CLIENT_EMAIL', 'newsletter', 'ID', com[3])[0][0]
            comments_dict[i]['avatar'] = take_data_where_ID('AVATAR_USER', 'newsletter', 'ID', com[3])[0][0]
            comments_dict[i]['data-time'] = format_date(com[4]) if lang=='pl' else format_date(com[4], False)
            
        theme = {
            'id': take_data_where_ID('ID', 'contents', 'ID', id_content)[0][0],
            'title': take_data_where_ID('TITLE', 'contents', 'ID', id_content)[0][0] if lang=='pl' else getLangText(take_data_where_ID('TITLE', 'contents', 'ID', id_content)[0][0]),
            'introduction': take_data_where_ID('CONTENT_MAIN', 'contents', 'ID', id_content)[0][0] if lang=='pl' else getLangText(take_data_where_ID('CONTENT_MAIN', 'contents', 'ID', id_content)[0][0]),
            'highlight': take_data_where_ID('HIGHLIGHTS', 'contents', 'ID', id_content)[0][0] if lang=='pl' else getLangText(take_data_where_ID('HIGHLIGHTS', 'contents', 'ID', id_content)[0][0]),
            'mainFoto': take_data_where_ID('HEADER_FOTO', 'contents', 'ID', id_content)[0][0],
            'contentFoto': take_data_where_ID('CONTENT_FOTO', 'contents', 'ID', id_content)[0][0],
            'additionalList': str(take_data_where_ID('BULLETS', 'contents', 'ID', id_content)[0][0]).split('#splx#') if lang=='pl' else str(getLangText(take_data_where_ID('BULLETS', 'contents', 'ID', id_content)[0][0])).replace('#SPLX#', '#splx#').split('#splx#'),
            'tags': str(take_data_where_ID('TAGS', 'contents', 'ID', id_content)[0][0]).split(', ') if lang=='pl' else str(getLangText(take_data_where_ID('TAGS', 'contents', 'ID', id_content)[0][0])).split(', '),
            'category': take_data_where_ID('CATEGORY', 'contents', 'ID', id_content)[0][0] if lang=='pl' else getLangText(take_data_where_ID('CATEGORY', 'contents', 'ID', id_content)[0][0]),
            'data': format_date(take_data_where_ID('DATE_TIME', 'contents', 'ID', id_content)[0][0]) if lang=='pl' else format_date(take_data_where_ID('DATE_TIME', 'contents', 'ID', id_content)[0][0], False),
            'author': take_data_where_ID('NAME_AUTHOR', 'authors', 'ID', id_author)[0][0],

            'author_about': take_data_where_ID('ABOUT_AUTHOR', 'authors', 'ID', id_author)[0][0] if lang=='pl' else getLangText(take_data_where_ID('ABOUT_AUTHOR', 'authors', 'ID', id_author)[0][0]),
            'author_avatar': take_data_where_ID('AVATAR_AUTHOR', 'authors', 'ID', id_author)[0][0],
            'author_facebook': take_data_where_ID('FACEBOOK', 'authors', 'ID', id_author)[0][0],
            'author_twitter': take_data_where_ID('TWITER_X', 'authors', 'ID', id_author)[0][0],
            'author_instagram': take_data_where_ID('INSTAGRAM', 'authors', 'ID', id_author)[0][0],

            'comments': comments_dict
        }
        daneList.append(theme)
    return daneList

def generator_daneDBList_short(lang='pl'):
    limit = 'LIMIT 5' if lang != 'pl' else ''

    # Pobieramy wszystkie dane za jednym razem
    query = f"""
        SELECT 
            c.ID, 
            c.TITLE, 
            c.HIGHLIGHTS, 
            c.HEADER_FOTO, 
            c.CATEGORY, 
            c.DATE_TIME, 
            a.NAME_AUTHOR
        FROM blog_posts bp
        JOIN contents c ON bp.CONTENT_ID = c.ID  
        JOIN authors a ON bp.AUTHOR_ID = a.ID  
        ORDER BY bp.ID DESC
        {limit};

    """

    all_posts = msq.connect_to_database(query)


    daneList = []
    for post in all_posts:
        id_content, title, highlights, mainFoto, category, date_time, author = post

        # Tłumaczenie raz, a nie dla każdego pola osobno
        if lang != 'pl':
            title, highlights, category = map(getLangText, (title, highlights, category))
            date_time = format_date(date_time, False)
        else:
            date_time = format_date(date_time)

        daneList.append({
            'id': id_content,
            'title': title,
            'highlight': highlights,
            'mainFoto': mainFoto,
            'category': category,
            'data': date_time,
            'author': author,
        })

    return daneList

def generator_daneDBList_short_old(lang='pl'):
    limit = ''
    if lang!='pl':
        limit = 'LIMIT 5'

    daneList = []
    took_allPost = msq.connect_to_database(f'SELECT * FROM blog_posts ORDER BY ID DESC {limit};') # take_data_table('*', 'blog_posts')
    for post in took_allPost:

        id_content = post[1]
        id_author = post[2]

        theme = {
            'id': take_data_where_ID('ID', 'contents', 'ID', id_content)[0][0],
            'title': take_data_where_ID('TITLE', 'contents', 'ID', id_content)[0][0] if lang=='pl' else getLangText(take_data_where_ID('TITLE', 'contents', 'ID', id_content)[0][0]),
            
            'highlight': take_data_where_ID('HIGHLIGHTS', 'contents', 'ID', id_content)[0][0] if lang=='pl' else getLangText(take_data_where_ID('HIGHLIGHTS', 'contents', 'ID', id_content)[0][0]),
            'mainFoto': take_data_where_ID('HEADER_FOTO', 'contents', 'ID', id_content)[0][0],
            
            'category': take_data_where_ID('CATEGORY', 'contents', 'ID', id_content)[0][0] if lang=='pl' else getLangText(take_data_where_ID('CATEGORY', 'contents', 'ID', id_content)[0][0]),
            'data': format_date(take_data_where_ID('DATE_TIME', 'contents', 'ID', id_content)[0][0]) if lang=='pl' else format_date(take_data_where_ID('DATE_TIME', 'contents', 'ID', id_content)[0][0], False),
            'author': take_data_where_ID('NAME_AUTHOR', 'authors', 'ID', id_author)[0][0],

        }
        daneList.append(theme)
    return daneList

def generator_jobs(lang='pl'):
    daneList = []
    
    try: took_allRecords = msq.connect_to_database(f'SELECT * FROM job_offers WHERE status=1 ORDER BY ID DESC;') 
    except: return []
    
    for rec in took_allRecords:

        theme = {
            'id': rec[0],
            'title': rec[1] if lang=='pl' else getLangText(rec[1]),
            'description': rec[2] if lang=='pl' else getLangText(rec[2]),
            'requirements_description': rec[3] if lang=='pl' else getLangText(rec[3]),
            'requirements': str(rec[4]).split('#splx#') if lang=='pl' else [getLangText(item) for item in str(rec[4]).split('#splx#')],
            'benefits': str(rec[5]).split('#splx#') if lang=='pl' else [getLangText(item) for item in str(rec[5]).split('#splx#')],
            'location': rec[6] if lang=='pl' else getLangText(rec[6]),
            'contact_email': rec[7],
            'employment_type': rec[8] if lang=='pl' else getLangText(rec[8]),
            'salary': rec[9] if lang=='pl' else getLangText(rec[9]),
            'start_date': format_date(rec[10]) if lang=='pl' else format_date(rec[10], False),
            'data': format_date(rec[11]) if lang=='pl' else format_date(rec[11], False),
            'brand': rec[12],
            'status': rec[13]
        }
        daneList.append(theme)
    return daneList

def generator_realized(lang='pl'):
    daneList = []
    
    try: took_allRecords = msq.connect_to_database(
        f"""
            SELECT *
            FROM realizacje_budownictwo
            ORDER BY r_finish DESC;
        """
        ) 
    except: return []
    for rec in took_allRecords:

        theme = {
            'id': rec[0],
            'kategoria': rec[1] if lang=='pl' else getLangText(rec[1]),
            'zdjecie': rec[2],
            'tytul_ogloszenia': rec[3] if lang=='pl' else getLangText(rec[3]),
            'opis': rec[4] if lang=='pl' else getLangText(rec[4]),
            'r_start': rec[5],
            'r_finish': rec[6],
            'data_aktualizacji': rec[7]
        }
        daneList.append(theme)
    return daneList

def generator_job_offer(id_offer, lang='pl'):
    try: rec = take_data_where_ID_AND_somethig('*', 'job_offers', 'id', id_offer, 'status', 1)[0]
    except: return []

    theme = {
            'id': rec[0],
            'title': rec[1] if lang=='pl' else getLangText(rec[1]),
            'description': rec[2] if lang=='pl' else getLangText(rec[2]),
            'requirements_description': rec[3] if lang=='pl' else getLangText(rec[3]),
            'requirements': str(rec[4]).split('#splx#') if lang=='pl' else [getLangText(item) for item in str(rec[4]).split('#splx#')],
            'benefits': str(rec[5]).split('#splx#') if lang=='pl' else [getLangText(item) for item in str(rec[5]).split('#splx#')],
            'location': rec[6] if lang=='pl' else getLangText(rec[6]),
            'contact_email': rec[7],
            'employment_type': rec[8] if lang=='pl' else getLangText(rec[8]),
            'salary': rec[9] if lang=='pl' else getLangText(rec[9]),
            'start_date': format_date(rec[10]) if lang=='pl' else format_date(rec[10], False),
            'data': format_date(rec[11]) if lang=='pl' else format_date(rec[11], False),
            'brand': rec[12],
            'status': rec[13]
        }
    return theme

def generator_daneDBList_prev_next(main_id):
    # msq.connect_to_database() zwraca listę tuple'i reprezentujących posty, np. [(1, 'Content1'), (2, 'Content2'), ...]
    took_allPost = msq.connect_to_database('SELECT ID FROM blog_posts ORDER BY ID DESC;')
    
    # Przekształcenie wyników z bazy danych do listy ID dla łatwiejszego wyszukiwania
    id_list = [post[0] for post in took_allPost]
    
    # Inicjalizacja słownika dla wyników
    pre_next = {
        'prev': None,
        'next': None
    }
    
    # Znajdowanie indeksu podanego ID w liście
    if main_id in id_list:
        current_index = id_list.index(main_id)
        
        # Sprawdzanie i przypisywanie poprzedniego ID, jeśli istnieje
        if current_index > 0:
            pre_next['prev'] = id_list[current_index - 1]
        
        # Sprawdzanie i przypisywanie następnego ID, jeśli istnieje
        if current_index < len(id_list) - 1:
            pre_next['next'] = id_list[current_index + 1]
    
    return pre_next

def generator_daneDBList_category(lang='pl'):
    # Pobranie kategorii z bazy danych
    took_allPost = msq.connect_to_database('SELECT CATEGORY FROM contents ORDER BY ID DESC;')

    # Tworzenie listy unikalnych kategorii
    unique_categories = set(post[0] for post in took_allPost)

    # Przetłumaczenie unikalnych kategorii tylko raz
    if lang != 'pl':
        translated_categories = {cat: getLangText(cat) for cat in unique_categories}
    else:
        translated_categories = {cat: cat for cat in unique_categories}

    # Zliczanie wystąpień przetłumaczonych kategorii
    cat_count = {}
    for post in took_allPost:
        category = translated_categories[post[0]]  # Używamy już przetłumaczonych wartości
        
        # Jeśli kategoria już istnieje, zwiększamy licznik
        if category in cat_count:
            cat_count[category]["cat_count"] += 1
        else:
            cat_count[category] = {"cat_count": 1, "org": post[0]}  # Inicjalizujemy kategorię

    # Tworzenie listy stringów z nazwami kategorii i ilością wystąpień
    cat_list = [f"{cat} ({count.get('cat_count', 0)})" for cat, count in cat_count.items()]

    return cat_list, cat_count

def generator_daneDBList_RecentPosts(main_id, amount = 3):
    # Pobieranie ID wszystkich postów oprócz main_id
    query = f"SELECT ID FROM contents WHERE ID != {main_id} ORDER BY ID DESC;"
    took_allPost = msq.connect_to_database(query)

    # Przekształcanie wyników zapytania na listę ID
    all_post_ids = [post[0] for post in took_allPost]

    # Losowanie unikalnych ID z listy (zakładając, że chcemy np. 5 losowych postów, lub mniej jeśli jest mniej dostępnych)
    num_posts_to_select = min(amount, len(all_post_ids))  
    posts = random.sample(all_post_ids, num_posts_to_select)

    return posts

def generator_daneDBList_one_post_id(id_post, lang='pl'):
    # Pobranie wszystkich danych jednym zapytaniem SQL
    query = f"""
        SELECT 
            bp.ID, 
            c.ID as content_id, 
            ANY_VALUE(c.TITLE) as TITLE, 
            ANY_VALUE(c.CONTENT_MAIN) as CONTENT_MAIN, 
            ANY_VALUE(c.HIGHLIGHTS) as HIGHLIGHTS, 
            ANY_VALUE(c.HEADER_FOTO) as HEADER_FOTO, 
            ANY_VALUE(c.CONTENT_FOTO) as CONTENT_FOTO, 
            ANY_VALUE(c.BULLETS) as BULLETS, 
            ANY_VALUE(c.TAGS) as TAGS, 
            ANY_VALUE(c.CATEGORY) as CATEGORY, 
            ANY_VALUE(c.DATE_TIME) as DATE_TIME,
            ANY_VALUE(a.NAME_AUTHOR) as NAME_AUTHOR, 
            ANY_VALUE(a.ABOUT_AUTHOR) as ABOUT_AUTHOR, 
            ANY_VALUE(a.AVATAR_AUTHOR) as AVATAR_AUTHOR, 
            ANY_VALUE(a.FACEBOOK) as FACEBOOK, 
            ANY_VALUE(a.TWITER_X) as TWITER_X, 
            ANY_VALUE(a.INSTAGRAM) as INSTAGRAM,
            COALESCE(
                GROUP_CONCAT(
                    JSON_OBJECT(
                        'id', cm.ID, 
                        'message', cm.COMMENT_CONNTENT,  
                        'user', nw.CLIENT_NAME, 
                        'e-mail', nw.CLIENT_EMAIL, 
                        'avatar', nw.AVATAR_USER,
                        'data-time', cm.DATE_TIME
                    )
                ), '[]'
            ) as comments
        FROM blog_posts bp
        JOIN contents c ON bp.CONTENT_ID = c.ID
        JOIN authors a ON bp.AUTHOR_ID = a.ID  
        LEFT JOIN comments cm ON cm.BLOG_POST_ID = bp.ID
        LEFT JOIN newsletter nw ON nw.ID = cm.AUTHOR_OF_COMMENT_ID
        WHERE bp.ID = {id_post}
        GROUP BY bp.ID
        ORDER BY bp.ID DESC
        LIMIT 1;
    """

    result = msq.connect_to_database(query)

    if not result:
        return []

    post = result[0]
    
    (
        id, id_content, title, content_main, highlights, mainFoto, contentFoto, 
        bullets, tags, category, date_time, author, author_about, author_avatar, 
        author_facebook, author_twitter, author_instagram, comments_json
    ) = post

    # Parsowanie JSON z komentarzami (jeśli są)
    comments_dict = {}

    if comments_json and comments_json.strip():
        try:
            comments_list = json.loads(f'[{comments_json}]')
            for i, comment in enumerate(comments_list):
                if comment['message'] is not None and comment['user'] is not None:
                    comments_dict[i] = {
                        'id': comment['id'],
                        'message': comment['message'] if lang == 'pl' else getLangText(comment['message']),
                        'user': comment['user'],
                        'e-mail': comment['e-mail'],
                        'avatar': comment['avatar'],
                        'data-time': format_date(comment['data-time']) if comment['data-time'] else "Brak daty",
                    }
        except json.JSONDecodeError:
            comments_dict = {}

    # Przetwarzanie listy dodatkowej (bullets) i tagów
    bullets_list = str(bullets).split('#splx#') if lang == 'pl' else str(getLangText(bullets)).replace('#SPLX#', '#splx#').split('#splx#')
    tags_list = str(tags).split(', ') if lang == 'pl' else str(getLangText(tags)).split(', ')

    # Tłumaczenie pól jeśli trzeba
    if lang != 'pl':
        title = getLangText(title)
        content_main = getLangText(content_main)
        highlights = getLangText(highlights)
        category = getLangText(category)
        author_about = getLangText(author_about)
        date_time = format_date(date_time, False)
    else:
        date_time = format_date(date_time)

    theme = {
        'id': id_content,
        'title': title,
        'introduction': content_main,
        'highlight': highlights,
        'mainFoto': mainFoto,
        'contentFoto': contentFoto,
        'additionalList': bullets_list,
        'tags': tags_list,
        'category': category,
        'data': date_time,
        'author': author,
        'author_about': author_about,
        'author_avatar': author_avatar,
        'author_facebook': author_facebook,
        'author_twitter': author_twitter,
        'author_instagram': author_instagram,
        'comments': comments_dict
    }

    return [theme]


def generator_daneDBList_one_post_id_old(id_post, lang='pl'):
    daneList = []
    took_allPost = msq.connect_to_database(f'SELECT * FROM blog_posts WHERE ID={id_post};') # take_data_table('*', 'blog_posts')
    for post in took_allPost:
        id = post[0]
        id_content = post[1]
        id_author = post[2]

        allPostComments = take_data_where_ID('*', 'comments', 'BLOG_POST_ID', id)
        comments_dict = {}
        for i, com in enumerate(allPostComments):
            comments_dict[i] = {}
            comments_dict[i]['id'] = com[0]
            comments_dict[i]['message'] = com[2] if lang=='pl' else getLangText(com[2])
            comments_dict[i]['user'] = take_data_where_ID('CLIENT_NAME', 'newsletter', 'ID', com[3])[0][0]
            comments_dict[i]['e-mail'] = take_data_where_ID('CLIENT_EMAIL', 'newsletter', 'ID', com[3])[0][0]
            comments_dict[i]['avatar'] = take_data_where_ID('AVATAR_USER', 'newsletter', 'ID', com[3])[0][0]
            comments_dict[i]['data-time'] = format_date(com[4]) if lang=='pl' else format_date(com[4], False)
            
        theme = {
            'id': take_data_where_ID('ID', 'contents', 'ID', id_content)[0][0],
            'title': take_data_where_ID('TITLE', 'contents', 'ID', id_content)[0][0] if lang=='pl' else getLangText(take_data_where_ID('TITLE', 'contents', 'ID', id_content)[0][0]),
            'introduction': take_data_where_ID('CONTENT_MAIN', 'contents', 'ID', id_content)[0][0] if lang=='pl' else getLangText(take_data_where_ID('CONTENT_MAIN', 'contents', 'ID', id_content)[0][0]),
            'highlight': take_data_where_ID('HIGHLIGHTS', 'contents', 'ID', id_content)[0][0] if lang=='pl' else getLangText(take_data_where_ID('HIGHLIGHTS', 'contents', 'ID', id_content)[0][0]),
            'mainFoto': take_data_where_ID('HEADER_FOTO', 'contents', 'ID', id_content)[0][0],
            'contentFoto': take_data_where_ID('CONTENT_FOTO', 'contents', 'ID', id_content)[0][0],
            'additionalList': str(take_data_where_ID('BULLETS', 'contents', 'ID', id_content)[0][0]).split('#splx#') if lang=='pl' else str(getLangText(take_data_where_ID('BULLETS', 'contents', 'ID', id_content)[0][0])).replace('#SPLX#', '#splx#').split('#splx#'),
            'tags': str(take_data_where_ID('TAGS', 'contents', 'ID', id_content)[0][0]).split(', ') if lang=='pl' else str(getLangText(take_data_where_ID('TAGS', 'contents', 'ID', id_content)[0][0])).split(', '),
            'category': take_data_where_ID('CATEGORY', 'contents', 'ID', id_content)[0][0] if lang=='pl' else getLangText(take_data_where_ID('CATEGORY', 'contents', 'ID', id_content)[0][0]),
            'data': format_date(take_data_where_ID('DATE_TIME', 'contents', 'ID', id_content)[0][0]) if lang=='pl' else format_date(take_data_where_ID('DATE_TIME', 'contents', 'ID', id_content)[0][0], False),
            'author': take_data_where_ID('NAME_AUTHOR', 'authors', 'ID', id_author)[0][0],

            'author_about': take_data_where_ID('ABOUT_AUTHOR', 'authors', 'ID', id_author)[0][0] if lang=='pl' else getLangText(take_data_where_ID('ABOUT_AUTHOR', 'authors', 'ID', id_author)[0][0]),
            'author_avatar': take_data_where_ID('AVATAR_AUTHOR', 'authors', 'ID', id_author)[0][0],
            'author_facebook': take_data_where_ID('FACEBOOK', 'authors', 'ID', id_author)[0][0],
            'author_twitter': take_data_where_ID('TWITER_X', 'authors', 'ID', id_author)[0][0],
            'author_instagram': take_data_where_ID('INSTAGRAM', 'authors', 'ID', id_author)[0][0],

            'comments': comments_dict
        }
        daneList.append(theme)
    return daneList

def format_job_count(count, lang='pl'):
    if lang=='pl':
        if count == 1:
            return f"Obecnie oferujemy {count} ofertę pracy."
        elif 2 <= count <= 4:
            return f"Obecnie oferujemy {count} oferty pracy."
        elif (count % 10 == 2 or count % 10 == 3 or count % 10 == 4) and not (12 <= count % 100 <= 14):
            return f"Obecnie oferujemy {count} oferty pracy."
        else:
            return f"Obecnie oferujemy {count} ofert pracy."
    else:
        if count == 1:
            return f"Currently, we offer {count} job opportunity."
        else:
            return f"Currently, we offer {count} job opportunities."
    
def mainDataGeneratorDict(select_key: str, lang:str = 'pl'):

    data = {
        "BLOG-ALLPOSTS-PL": generator_daneDBList(lang),
        "BLOG-ALLPOSTS-EN": generator_daneDBList(lang),
        "BLOG-SHORT-PL": generator_daneDBList_short(lang),
        "BLOG-SHORT-EN": generator_daneDBList_short(lang),
        # "BLOG-FOOTER-PL": generator_daneDBList_3('pl'),
        # "BLOG-FOOTER-EN": generator_daneDBList_3('en'),
        "TEAM-ALL-PL": generator_teamDB(lang),
        "TEAM-ALL-EN": generator_teamDB(lang),
        "SUBS-ALL-PL": generator_subsDataDB()
    }

    return data.get(select_key, [])


logFileName = '/home/johndoe/app/dmdbudownictwo/logs/access.log'  # 🔁

# Konfiguracja loggera
logging.basicConfig(filename=logFileName, level=logging.INFO,
                    format='%(asctime)s - %(message)s', filemode='a')

# Funkcja do logowania informacji o zapytaniu
def log_request():
    ip_address = request.remote_addr
    date_time = datetime.now()
    endpoint = request.endpoint or request.path  # fallback jeśli brak endpointu
    method = request.method

    logging.info(f'IP: {ip_address}, Time: {date_time}, Endpoint: {endpoint}, Method: {method}')

@app.before_request
def before_request_logging():
    log_request()

############################
##      ######           ###
##      ######           ###
##     ####              ###
##     ####              ###
##    ####               ###
##    ####               ###
##   ####                ###
##   ####                ###
#####                    ###
#####                    ###
##   ####                ###
##   ####                ###
##    ####               ###
##    ####               ###
##     ####              ###
##     ####              ###
##      ######           ###
##      ######           ###
############################

# @app.route('/.well-known/pki-validation/certum.txt')
# def download_file():
#     return send_from_directory(app.root_path, 'certum.txt')

@app.template_filter('smart_truncate')
def smart_truncate(content, length=400):
    if len(content) <= length:
        return content
    else:
        # Znajdujemy miejsce, gdzie jest koniec pełnego słowa, nie przekraczając maksymalnej długości
        truncated_content = content[:length].rsplit(' ', 1)[0]
        return f"{truncated_content}..."

@app.route('/pl')
def langPl():
    if session.get('lang') != 'pl':  # Sprawdzenie, czy nastąpiła zmiana języka
        session['lang'] = 'pl'
        # Wyczyść dane związane z językiem, aby wymusić ich ponowne załadowanie
        session.pop('TEAM-ALL', None)
        session.pop('BLOG-SHORT', None)
        session.pop('CAREER-ALL', None)
        session.pop('BLOG-CATEGORY', None)
        session.pop('BLOG-ALL', None)
        session.pop('PROJECTS-ALL', None)

    session['lang'] = 'pl'
    if 'page' not in session:
        return redirect(url_for(f'index'))
    else:
        # print(session["page"])
        if session['page'] == 'blogOne':
            return redirect(url_for(f'blogs'))
        elif session['page'] == 'karieraOne':
            return redirect(url_for(f'kariera'))
        else:
            return redirect(url_for(f'{session["page"]}'))

@app.route('/en')
def langEn():
    if session.get('lang') != 'en':  # Sprawdzenie, czy nastąpiła zmiana języka
        session['lang'] = 'en'
        # Wyczyść dane związane z językiem, aby wymusić ich ponowne załadowanie
        session.pop('TEAM-ALL', None)
        session.pop('BLOG-SHORT', None)
        session.pop('CAREER-ALL', None)
        session.pop('BLOG-CATEGORY', None)
        session.pop('BLOG-ALL', None)
        session.pop('PROJECTS-ALL', None)

    if 'page' not in session:
        return redirect(url_for(f'index'))
    else:
        # print(session["page"])
        if session['page'] == 'blogOne':
            return redirect(url_for(f'blogs'))
        elif session['page'] == 'karieraOne':
            return redirect(url_for(f'kariera'))
        else:
            return redirect(url_for(f'{session["page"]}'))

@app.route('/')
def index():
    
    session['page'] = 'index'
    if 'lang' not in session:
        session['lang'] = 'pl'

    selected_language = session['lang']

    if selected_language == 'en':
        pageTitle = 'Home Page'
    else:
        pageTitle = 'Strona Główna'

    if f'TEAM-ALL' not in session:
        team_list = generator_teamDB(selected_language)
        print(selected_language)
        print(team_list)
        session[f'TEAM-ALL'] = team_list
    else:
        team_list = session[f'TEAM-ALL']

    fourListTeam = []
    for i, member in enumerate(team_list):
        if  i < 4: fourListTeam.append(member)
        
    if f'BLOG-SHORT' not in session:
        blog_post = generator_daneDBList_short(selected_language)
        session[f'BLOG-SHORT'] = blog_post
    else:
        blog_post = session[f'BLOG-SHORT']
    
    blog_post_three = []
    for i, member in enumerate(blog_post):
        if  i < 3: blog_post_three.append(member)

    return render_template(
        f'index-{selected_language}.html',
        pageTitle=pageTitle,
        fourListTeam=fourListTeam, 
        blog_post_three=blog_post_three,
        )

@app.route('/o-nas')
def oNas():
    session['page'] = 'oNnas'
    
    if 'lang' not in session:
        session['lang'] = 'pl'

    selected_language = session['lang']

    if selected_language == 'en':
        pageTitle = 'About Us'
    else:
        pageTitle = 'O nas'

    return render_template(
        f'onas-{selected_language}.html',
        pageTitle=pageTitle
        )

@app.route('/struktura', methods=['GET'])
def struktura():
    session['page'] = 'struktura'

    if 'lang' not in session:
        session['lang'] = 'pl'

    selected_language = session['lang']

    if selected_language == 'en':
        pageTitle = 'Structure'
    else:
        pageTitle = 'Struktura'
    
    if 'target' in request.args:
        if request.args['target'] in [
            'budownictwo', 'domy', 'elitehome', 
            'inwestycje', 'instalacje', 'development']:
            targetPage = request.args['target']
        else: targetPage = "struktura"
    else:
        targetPage = "struktura"

    return render_template(
        f'{targetPage}-{selected_language}.html',
        pageTitle=pageTitle
        )

@app.route('/jak-pracujemy')
def jakPracujemy():
    session['page'] = 'jakPracujemy'

    if 'lang' not in session:
        session['lang'] = 'pl'

    selected_language = session['lang']

    if selected_language == 'en':
        pageTitle = 'How We Work'
    else:
        pageTitle = 'Jak Pracujemy'
    
    return render_template(
        f'pracujemy-{selected_language}.html',
        pageTitle=pageTitle
        )

@app.route('/realizacje')
def realizacje():
    session['page'] = 'realizacje'
    
    if 'lang' not in session:
        session['lang'] = 'pl'

    selected_language = session['lang']

    if selected_language == 'en':
        pageTitle = 'Projects'
    else:
        pageTitle = 'Realizacje'

    if f'PROJECTS-ALL' not in session:
        projects = generator_realized(selected_language)
        session[f'PROJECTS-ALL'] = projects
    else:
        projects = session[f'PROJECTS-ALL']

    return render_template(
        f'realizacje-{selected_language}.html',
        projects=projects,
        pageTitle=pageTitle
        )

@app.route('/kontakt')
def kontakt():
    session['page'] = 'kontakt'
    if 'lang' not in session:
        session['lang'] = 'pl'

    selected_language = session['lang']

    if selected_language == 'en':
        pageTitle = 'Contact'
    else:
        pageTitle = 'Kontakt'

    return render_template(
        f'kontakt-{selected_language}.html',
        pageTitle=pageTitle
        )

@app.route('/kariera')
def kariera():
    session['page'] = 'kariera'
    
    if 'lang' not in session:
        session['lang'] = 'pl'

    selected_language = session['lang']

    if selected_language == 'en':
        pageTitle = 'Career'
    else:
        pageTitle = 'Kariera'

    if f'CAREER-ALL' not in session:
        jobs_took = generator_jobs(selected_language)
        session[f'CAREER-ALL'] = jobs_took
    else:
        jobs_took = session[f'CAREER-ALL']


    found = len(jobs_took)
    job_count_message = format_job_count(found, selected_language)
    

    # Ustawienia paginacji
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    total = len(jobs_took)
    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap4')

    # Pobierz tylko odpowiednią ilość postów na aktualnej stronie
    jobs = jobs_took[offset: offset + per_page]

    return render_template(
        f'kariera-{selected_language}.html',
        pageTitle=pageTitle,
        job_count_message=job_count_message,
        jobs=jobs,
        pagination=pagination
        )


@app.route('/kariera-one', methods=['GET'])
def karieraOne():
    session['page'] = 'karieraOne'
    if 'lang' not in session:
        session['lang'] = 'pl'

    selected_language = session['lang']

    if selected_language == 'en':
        pageTitle = 'Career'
    else:
        pageTitle = 'Kariera'

    if 'job' in request.args:
        job_id = request.args.get('job')
        try: job_id_int = int(job_id)
        except ValueError: return redirect(url_for('kariera'))
    else:
        return redirect(url_for(f'kariera'))
    
    choiced = generator_job_offer(job_id_int, selected_language)
    if not len(choiced):
        return redirect(url_for(f'kariera'))
    
    def format_header(title):
        # Rozdziel tytuł na pierwsze słowo i resztę
        words = title.split(' ', 1)  # Rozdziela tylko na 2 części
        if len(words) > 1:
            return f'<span class="theme_color">{words[0]}</span> {words[1]}'
        else:
            return f'<span class="theme_color">{words[0]}</span>'
        
    choiced['title_split'] = format_header(choiced['title'])
    print(choiced)
    return render_template(
        f'kariera-one-{selected_language}.html',
        pageTitle=pageTitle,
        choiced=choiced
        )

# @app.route('/my-zespol')
# def myZespol():
#     session['page'] = 'myZespol'
#     pageTitle = 'Zespół'


#     if f'TEAM-ALL' not in session:
#         team_list = generator_teamDB()
#         session[f'TEAM-ALL'] = team_list
#     else:
#         team_list = session[f'TEAM-ALL']

#     fullListTeam = []
#     for i, member in enumerate(team_list):
#        fullListTeam.append(member)
    
#     return render_template(
#         f'myZespol.html',
#         pageTitle=pageTitle,
        
#         fullListTeam=fullListTeam
#         )

@app.route('/blogs')
def blogs():
    session['page'] = 'blogs'

    if 'lang' not in session:
        session['lang'] = 'pl'

    selected_language = session['lang']

    if f'BLOG-CATEGORY' not in session:
        cats = generator_daneDBList_category(selected_language)
        session[f'BLOG-CATEGORY'] = cats
    else:
        cats = session[f'BLOG-CATEGORY']
    
    if f'BLOG-SHORT' not in session:
        blog_post = generator_daneDBList_short(selected_language)
        session[f'BLOG-SHORT'] = blog_post
    else:
        blog_post = session[f'BLOG-SHORT']

    pageTitle = 'Blog'

    # blog_post = generator_daneDBList()

    # Ustawienia paginacji
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    total = len(blog_post)
    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap4')

    # Pobierz tylko odpowiednią ilość postów na aktualnej stronie
    posts = blog_post[offset: offset + per_page]

    # cats = generator_daneDBList_category()
    cat_dict = cats[1]
    take_id_rec_pos = generator_daneDBList_RecentPosts(0)
    recentPosts = []
    for idp in take_id_rec_pos:
        t_post = generator_daneDBList_one_post_id(idp, selected_language)[0]
        theme = {
            'id': t_post['id'],
            'title': t_post['title'],
            'mainFoto': t_post['mainFoto'],
            'contentFoto': t_post['contentFoto'],
            'category': t_post['category'],
            'author': t_post['author'],
            'data': t_post['data']
        }
        recentPosts.append(theme)

    return render_template(
        f'blogs-{selected_language}.html',
        pageTitle=pageTitle,
        cat_dict=cat_dict,
        recentPosts=recentPosts,
        pagination=pagination,
        posts=posts
        )

@app.route('/blog-one', methods=['GET'])
def blogOne():
    session['page'] = 'blogOne'

    if 'lang' not in session:
        session['lang'] = 'pl'

    selected_language = session['lang']

    if f'BLOG-CATEGORY' not in session:
        cats = generator_daneDBList_category(selected_language)
        session[f'BLOG-CATEGORY'] = cats
    else:
        cats = session[f'BLOG-CATEGORY']
    
    
    if 'post' in request.args:
        post_id = request.args.get('post')
        try: post_id_int = int(post_id)
        except ValueError: return redirect(url_for('blogs'))
    else:
        return redirect(url_for(f'blogs'))
    
    choiced = generator_daneDBList_one_post_id(post_id_int, selected_language)[0]
    choiced['len'] = len(choiced['comments'])
    pageTitle = choiced['title']

    pre_next = {
        'prev': generator_daneDBList_prev_next(post_id_int)['prev'],  
        'next': generator_daneDBList_prev_next(post_id_int)['next']
        }


    cat_dict = cats[1]
    take_id_rec_pos = generator_daneDBList_RecentPosts(post_id_int)
    recentPosts = []
    for idp in take_id_rec_pos:
        t_post = generator_daneDBList_one_post_id(idp, selected_language)[0]
        theme = {
            'id': t_post['id'],
            'title': t_post['title'],
            'mainFoto': t_post['mainFoto'],
            'contentFoto': t_post['contentFoto'],
            'category': t_post['category'],
            'author': t_post['author'],
            'data': t_post['data']
        }
        recentPosts.append(theme)
    

    return render_template(
        f'blog-{selected_language}.html',
        pageTitle=pageTitle,
        choiced=choiced,
        pre_next=pre_next,
        cat_dict=cat_dict,
        recentPosts=recentPosts
        )


@app.errorhandler(404)
def page_not_found(e):
    # Tutaj możesz przekierować do dowolnej trasy, którą chcesz wyświetlić jako stronę błędu 404.
    return redirect(url_for(f'index'))


@app.route('/find-by-category', methods=['GET'])
def findByCategory():
    session['page'] = 'findByCategory'
    if 'lang' not in session:
        session['lang'] = 'pl'

    selected_language = session['lang']

    query = request.args.get('category')
    if not query:
        print('Błąd requesta')
        return redirect(url_for('index'))
        
    sqlQuery = """
                SELECT ID FROM contents 
                WHERE CATEGORY LIKE %s 
                ORDER BY ID DESC;
                """
    params = (f'%{query}%', )
    results = msq.safe_connect_to_database(sqlQuery, params)
    if selected_language == 'pl':
        pageTitle = f'Wyniki wyszukiwania dla kategorii {query}'
    else:
        pageTitle = f'Search results'

    searchResults = []
    for find_id in results:
        post_id = int(find_id[0])
        t_post = generator_daneDBList_one_post_id(post_id, selected_language)[0]
        theme = {
            'id': t_post['id'],
            'title': t_post['title'],
            'mainFoto': t_post['mainFoto'],
            'introduction': smart_truncate(t_post['introduction'], 200),
            'category': t_post['category'],
            'author': t_post['author'],
            'data': t_post['data']
        }
        searchResults.append(theme)

    found = len(searchResults)

    # Ustawienia paginacji
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    total = len(searchResults)
    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap4')

    # Pobierz tylko odpowiednią ilość postów na aktualnej stronie
    posts = searchResults[offset: offset + per_page]


    return render_template(
        f"searchBlog-{selected_language}.html",
        pageTitle=pageTitle,
        posts=posts,
        found=found,
        pagination=pagination
        )


@app.route('/search-post-blog', methods=['GET', 'POST']) #, methods=['GET', 'POST']
def searchBlog():
    session['page'] = 'searchBlog'
    if 'lang' not in session:
        session['lang'] = 'pl'

    selected_language = session['lang']

    if request.method == "POST":
        query = request.form["query"]
        if not query:
            print('Błąd requesta')
            return redirect(url_for('index'))
        if selected_language != "pl":
            query_en = query
            query = getLangText(query_en, dest='pl')
        session['last_search'] = query

    elif 'last_search' in session:
        query = session['last_search']
    else:
        print('Błąd requesta')
        return redirect(url_for('index'))  # Uwaga: poprawiłem 'f' na 'index'

    sqlQuery = """
                SELECT ID FROM contents 
                WHERE TITLE LIKE %s 
                OR CONTENT_MAIN LIKE %s 
                OR HIGHLIGHTS LIKE %s 
                OR BULLETS LIKE %s 
                ORDER BY ID DESC;
                """
    params = (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%')
    results = msq.safe_connect_to_database(sqlQuery, params)
    if selected_language == 'pl':
        pageTitle = f'Wyniki wyszukiwania dla kategorii {query}'
    else:
        pageTitle = f'Search results for category {query_en}'
    # pageTitle = f'Wyniki wyszukiwania dla {query}'

    searchResults = []
    for find_id in results:
        post_id = int(find_id[0])
        t_post = generator_daneDBList_one_post_id(post_id, selected_language)[0]
        theme = {
            'id': t_post['id'],
            'title': t_post['title'],
            'mainFoto': t_post['mainFoto'],
            'introduction': smart_truncate(t_post['introduction'], 200),
            'category': t_post['category'],
            'author': t_post['author'],
            'data': t_post['data']
        }
        searchResults.append(theme)

    found = len(searchResults)

    # Ustawienia paginacji
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    total = len(searchResults)
    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap4')

    # Pobierz tylko odpowiednią ilość postów na aktualnej stronie
    posts = searchResults[offset: offset + per_page]


    return render_template(
        f"searchBlog-{selected_language}.html",
        pageTitle=pageTitle,
        posts=posts,
        found=found,
        pagination=pagination
        )

@app.route('/send-mess-pl', methods=['POST'])
def sendMess():

    if request.method == 'POST':
        form_data = request.json
        CLIENT_NAME = form_data['name']
        CLIENT_SUBJECT = form_data['subject']
        CLIENT_EMAIL = form_data['email']
        CLIENT_MESSAGE = form_data['message']

        if 'condition' not in form_data:
            return jsonify(
                {
                    'success': False, 
                    'message': f'Musisz zaakceptować naszą politykę prywatności!'
                })
        if CLIENT_NAME == '':
            return jsonify(
                {
                    'success': False, 
                    'message': f'Musisz podać swoje Imię i Nazwisko!'
                })
        if CLIENT_SUBJECT == '':
            return jsonify(
                {
                    'success': False, 
                    'message': f'Musisz podać temat wiadomości!'
                })
        if CLIENT_EMAIL == '' or '@' not in CLIENT_EMAIL or '.' not in CLIENT_EMAIL or len(CLIENT_EMAIL) < 7:
            return jsonify(
                {
                    'success': False, 
                    'message': f'Musisz podać adres email!'
                })
        if CLIENT_MESSAGE == '':
            return jsonify(
                {
                    'success': False, 
                    'message': f'Musisz podać treść wiadomości!'
                })

        # --- meta z żądania (Flask/FastAPI) ---
        ref = request.headers.get('Referer')
        ua  = request.headers.get('User-Agent')
        # Host: w Flask jest też request.host; w FastAPI/Starlette z ASGI bywa tylko nagłówek
        host = request.headers.get('Host') or getattr(request, 'host', None)

        # Realne IP z uwzględnieniem proxy/CDN:
        xff = request.headers.get('X-Forwarded-For', '')
        ip_from_xff = xff.split(',')[0].strip() if xff else None
        ip = (request.headers.get('CF-Connecting-IP') or ip_from_xff or request.remote_addr)

        zapytanie_sql = '''
            INSERT INTO contact 
                (CLIENT_NAME, CLIENT_EMAIL, SUBJECT, MESSAGE, DONE, remote_ip, referer, user_agent, source_host) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        '''
        dane = (
            CLIENT_NAME,
            CLIENT_EMAIL,
            CLIENT_SUBJECT,
            CLIENT_MESSAGE,
            1,
            ip,
            ref,
            ua,
            host
        )
    
        if msq.insert_to_database(zapytanie_sql, dane):
            return jsonify(
                {
                    'success': True, 
                    'message': f'Wiadomość została wysłana!'
                })
        else:
            return jsonify(
                {
                    'success': False, 
                    'message': f'Wystąpił problem z wysłaniem Twojej wiadomości, skontaktuj się w inny sposób lub spróbuj później!'
                })

    return redirect(url_for('index'))

@app.route('/add-subs-pl', methods=['POST'])
def addSubs():
    subsList = generator_subsDataDB() # pobieranie danych subskrybentów

    if request.method == 'POST':
        form_data = request.json

        SUB_NAME = form_data['Imie']
        SUB_EMAIL = form_data['Email']
        USER_HASH = secrets.token_hex(20)

        allowed = True
        for subscriber in subsList:
            if subscriber['email'] == SUB_EMAIL:
                allowed = False

        if allowed:
            # --- meta z żądania (Flask/FastAPI) ---
            ref = request.headers.get('Referer')
            ua  = request.headers.get('User-Agent')
            host = request.headers.get('Host') or getattr(request, 'host', None)

            # Realne IP z uwzględnieniem proxy/CDN:
            xff = request.headers.get('X-Forwarded-For', '')
            ip_from_xff = xff.split(',')[0].strip() if xff else None
            ip = (request.headers.get('CF-Connecting-IP') or ip_from_xff or request.remote_addr)

            # (opcjonalnie) bardzo prosty anty-bot: wymagaj swojej domeny w referer + niepusty UA
            # if (not ua or not ua.strip()) or (ref and 'dmdbudownictwo.pl' not in ref):
            #     abort(403)

            zapytanie_sql = '''
                INSERT INTO newsletter 
                    (CLIENT_NAME, CLIENT_EMAIL, ACTIVE, USER_HASH, remote_ip, referer, user_agent, source_host) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            '''
            dane = (SUB_NAME, SUB_EMAIL, 0, USER_HASH, ip, ref, ua, host)
            if msq.insert_to_database(zapytanie_sql, dane):
                return jsonify(
                    {
                        'success': True, 
                        'message': f'Zgłoszenie nowego subskrybenta zostało wysłane, aktywuj przez email!'
                    })
            else:
                return jsonify(
                {
                    'success': False, 
                    'message': f'Niestety nie udało nam się zarejestrować Twojej subskrypcji z powodu niezidentyfikowanego błędu!'
                })
        else:
            return jsonify(
                {
                    'success': False, 
                    'message': f'Podany adres email jest już zarejestrowany!'
                })
    return redirect(url_for('index'))

@app.route('/add-comm-pl', methods=['POST'])
def addComm():
    subsList = generator_subsDataDB() # pobieranie danych subskrybentów

    if request.method == 'POST':
        form_data = request.json
        # print(form_data)
        SUB_ID = None
        SUB_NAME = form_data['Name']
        SUB_EMAIL = form_data['Email']
        SUB_COMMENT = form_data['Comment']
        POST_ID = form_data['id']
        allowed = False
        for subscriber in subsList:
            if subscriber['email'] == SUB_EMAIL and subscriber['name'] == SUB_NAME and int(subscriber['status']) == 1:
                allowed = True
                SUB_ID = subscriber['id']
                break
        if allowed and SUB_ID:
            # print(form_data)
            zapytanie_sql = '''
                    INSERT INTO comments 
                        (BLOG_POST_ID, COMMENT_CONNTENT, AUTHOR_OF_COMMENT_ID) 
                        VALUES (%s, %s, %s);
                    '''
            dane = (POST_ID, SUB_COMMENT, SUB_ID)
            if msq.insert_to_database(zapytanie_sql, dane):
                return jsonify({'success': True, 'message': f'Post został skomentowany!'})
        else:
            return jsonify({'success': False, 'message': f'Musisz być naszym subskrybentem żeby komentować naszego bloga!'})


        
    return redirect(url_for('blogs'))

@app.route('/subpage', methods=['GET'])
def subpage():
    session['page'] = 'subpage'

    if 'lang' not in session:
        session['lang'] = 'pl'

    selected_language = session['lang']

    allowed_targets = ['polityka', 'zasady', 'pomoc']
    translations = {
        'en': {'polityka': 'Privacy Policy', 'zasady': 'Terms of Use', 'pomoc': 'Help'},
        'pl': {'polityka': 'Polityka prywatności', 'zasady': 'Zasady użytkowania', 'pomoc': 'Pomoc'}
    }

    targetPage = request.args.get('target', 'pomoc')
    if targetPage not in allowed_targets:
        targetPage = 'pomoc'

    pageTitle = translations.get(selected_language, translations['pl'])[targetPage]

    return render_template(
        f'{targetPage}-{selected_language}.html',
        pageTitle=pageTitle
        )

# @app.route('/konkurs-quiz-2025')
# def regulaminQuiz():
#     session['page'] = 'regulaminQuiz'

#     if 'lang' not in session:
#         session['lang'] = 'pl'

#     selected_language = session['lang']

#     if selected_language == 'en':
#         pageTitle = 'Quiz 2025'
#     else:
#         pageTitle = 'Quiz 2025'
    
#     return render_template(
#         f'konkurs-quiz-{selected_language}.html',
#         pageTitle=pageTitle
#         )

# ================== ANKIETA SZKOLNA ==================
# from zoneinfo import ZoneInfo
# import os, json, fcntl

# DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
# os.makedirs(DATA_DIR, exist_ok=True)
# DATA_FILE = os.path.join(DATA_DIR, 'spotkanie-szkolne.jsonl')

# def client_ip():
#     # uwzględnij reverse proxy
#     fwd = request.headers.get('X-Forwarded-For', '')
#     if fwd:
#         return fwd.split(',')[0].strip()
#     return request.remote_addr

# def append_jsonl(path: str, obj: dict):
#     with open(path, 'a', encoding='utf-8') as f:
#         # lock na czas dopisania
#         fcntl.flock(f.fileno(), fcntl.LOCK_EX)
#         f.write(json.dumps(obj, ensure_ascii=False) + '\n')
#         f.flush()
#         os.fsync(f.fileno())
#         fcntl.flock(f.fileno(), fcntl.LOCK_UN)

# @app.post('/api/ankieta/spotkanie-szkolne')
# def ankieta_spotkanie():
#     # przyjmij JSON lub form-data
#     if request.is_json:
#         payload = request.get_json(silent=True) or {}
#     else:
#         # mapuj z pól formularza
#         form = request.form
#         payload = {
#             "imie_nazwisko": form.get('imie_nazwisko', '').strip(),
#             "terminy": request.form.getlist('terminy'),
#             "godziny": request.form.getlist('godziny'),
#             "miejsca": request.form.getlist('miejsca'),
#             "miejsce_inne": form.get('miejsce_inne', '').strip()
#         }

#     name = (payload.get('imie_nazwisko') or '').strip()
#     if not name:
#         return jsonify({"ok": False, "error": "missing_name"}), 400

#     terminy = payload.get('terminy') or []
#     godziny = payload.get('godziny') or []
#     miejsca = payload.get('miejsca') or []
#     miejsce_inne = (payload.get('miejsce_inne') or '').strip()
#     if miejsce_inne:
#         miejsca = list(miejsca) + [miejsce_inne]

#     entry = {
#         "submitted_at": datetime.now(ZoneInfo("Europe/Warsaw")).isoformat(),
#         "imie_nazwisko": name,
#         "terminy": terminy,
#         "godziny": godziny,
#         "miejsca": miejsca,
#         "client": {
#             "ip": client_ip(),
#             "user_agent": request.headers.get('User-Agent', '')
#         }
#     }

#     try:
#         append_jsonl(DATA_FILE, entry)
#         resp = jsonify({"ok": True})
#         resp.headers['Cache-Control'] = 'no-store'
#         return resp, 200
#     except Exception as e:
#         # do logów można dodać print(e) / logger
#         return jsonify({"ok": False, "error": "write_failed"}), 500

# @app.route('/ankieta-szkolna')
# def ankieta_szkolna():
#     return render_template(f'ankieta.html')

if __name__ == '__main__':
    # app.run(debug=True, port=5050)
    app.run(debug=True, host='0.0.0.0', port=5050)