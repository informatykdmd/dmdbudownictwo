from flask import Flask, render_template, redirect, url_for, jsonify, session, request, send_from_directory
from flask_paginate import Pagination, get_page_args
import mysqlDB as msq
import secrets
from datetime import datetime
from googletrans import Translator
import random
from flask_session import Session

from markupsafe import Markup

app = Flask(__name__)
app.config['PER_PAGE'] = 6
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SESSION_TYPE'] = 'filesystem'  # Możesz wybrać inny backend, np. 'redis', 'sqlalchemy', itp.
Session(app)

def getLangText(text):
    """Funkcja do tłumaczenia tekstu z polskiego na angielski"""
    translator = Translator()
    translation = translator.translate(str(text), dest='en')
    return translation.text

def format_date(date_input, pl=True):
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
        # dostosowane dla dmd inwestycje
        if data[4] == 'dmd budownictwo':
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
    daneList = []
    took_allPost = msq.connect_to_database(f'SELECT * FROM blog_posts ORDER BY ID DESC;') # take_data_table('*', 'blog_posts')
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
    daneList = []
    took_allPost = msq.connect_to_database(f'SELECT * FROM blog_posts ORDER BY ID DESC;') # take_data_table('*', 'blog_posts')
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

def generator_jobs():
    daneList = []
    
    try: took_allRecords = msq.connect_to_database(f'SELECT * FROM job_offers WHERE status=1 ORDER BY ID DESC;') 
    except: return []
    
    for rec in took_allRecords:

        theme = {
            'id': rec[0],
            'title': rec[1],
            'description': rec[2],
            'requirements_description': rec[3],
            'requirements': rec[4],
            'benefits': rec[5],
            'location': rec[6],
            'contact_email': rec[7],
            'employment_type': rec[8],
            'salary': rec[9],
            'start_date': rec[10],
            'data': format_date(rec[11]),
            'brand': rec[12],
            'status': rec[13]
        }
        daneList.append(theme)
    return daneList

def generator_job_offer(id_offer):
    try: offer = take_data_where_ID_AND_somethig('*', 'job_offers', 'id', id_offer, 'status', 1)[0]
    except: return []

    theme = {
            'id': offer[0],
            'title': offer[1],
            'description': offer[2],
            'requirements_description': offer[3],
            'requirements': str(offer[4]).split('#splx#'), # lista
            'benefits': str(offer[5]).split('#splx#'), # lista
            'location': offer[6],
            'contact_email': offer[7],
            'employment_type': offer[8],
            'salary': offer[9],
            'start_date': format_date(offer[10]),
            'data': format_date(offer[11]),
            'brand': offer[12],
            'status': offer[13]
        }
    return theme

def generator_daneDBList_prev_next(main_id):
    # Załóżmy, że msq.connect_to_database() zwraca listę tuple'i reprezentujących posty, np. [(1, 'Content1'), (2, 'Content2'), ...]
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

def generator_daneDBList_cetegory():
    # Pobranie kategorii z bazy danych
    took_allPost = msq.connect_to_database('SELECT CATEGORY FROM contents ORDER BY ID DESC;')
    
    # Zliczanie wystąpień każdej kategorii
    cat_count = {}
    for post in took_allPost:
        category = post[0]
        if category in cat_count:
            cat_count[category] += 1
        else:
            cat_count[category] = 1

    # Tworzenie listy stringów z nazwami kategorii i ilością wystąpień
    cat_list = [f"{cat} ({count})" for cat, count in cat_count.items()]
    cat_dict = cat_count
    
    return cat_list, cat_dict

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

def format_job_count(count):
    if count == 1:
        return f"Obecnie oferujemy {count} ofertę pracy."
    elif 2 <= count <= 4:
        return f"Obecnie oferujemy {count} oferty pracy."
    elif (count % 10 == 2 or count % 10 == 3 or count % 10 == 4) and not (12 <= count % 100 <= 14):
        return f"Obecnie oferujemy {count} oferty pracy."
    else:
        return f"Obecnie oferujemy {count} ofert pracy."

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


@app.route('/')
def index():
    session['page'] = 'index'
    pageTitle = 'Strona Główna'

    if f'TEAM-ALL' not in session:
        team_list = generator_teamDB()
        session[f'TEAM-ALL'] = team_list
    else:
        team_list = session[f'TEAM-ALL']

    fourListTeam = []
    for i, member in enumerate(team_list):
        if  i < 4: fourListTeam.append(member)
        
    if f'BLOG-SHORT' not in session:
        blog_post = generator_daneDBList_short()
        session[f'BLOG-SHORT'] = blog_post
    else:
        blog_post = session[f'BLOG-SHORT']
    
    blog_post_three = []
    for i, member in enumerate(blog_post):
        if  i < 3: blog_post_three.append(member)

    return render_template(
        f'index.html',
        pageTitle=pageTitle,
        fourListTeam=fourListTeam, 
        blog_post_three=blog_post_three,
        )

@app.route('/o-nas')
def oNas():
    session['page'] = 'O nas'
    pageTitle = 'O nas'

    return render_template(
        f'onas.html',
        pageTitle=pageTitle
        )

@app.route('/struktura', methods=['GET'])
def struktura():
    session['page'] = 'struktura'
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
        f'{targetPage}.html',
        pageTitle=pageTitle
        )

@app.route('/jak-pracujemy')
def jakPracujemy():
    session['page'] = 'Jak Pracujemy'
    pageTitle = 'Jak Pracujemy'

    return render_template(
        f'pracujemy.html',
        pageTitle=pageTitle
        )

@app.route('/realizacje')
def realizacje():
    session['page'] = 'realizacje'
    pageTitle = 'Realizacje'

    return render_template(
        f'realizacje.html',
        pageTitle=pageTitle
        )

@app.route('/kontakt')
def kontakt():
    session['page'] = 'kontakt'
    pageTitle = 'kontakt'

    return render_template(
        f'kontakt.html',
        pageTitle=pageTitle
        )

@app.route('/kariera')
def kariera():
    session['page'] = 'kariera'
    pageTitle = 'Kariera'

    jobs_took = generator_jobs()

    found = len(jobs_took)
    job_count_message = format_job_count(found)
    

    # Ustawienia paginacji
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    total = len(jobs_took)
    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap4')

    # Pobierz tylko odpowiednią ilość postów na aktualnej stronie
    jobs = jobs_took[offset: offset + per_page]

    return render_template(
        f'kariera.html',
        pageTitle=pageTitle,
        job_count_message=job_count_message,
        jobs=jobs,
        pagination=pagination
        )


@app.route('/kariera-one', methods=['GET'])
def karieraOne():
    session['page'] = 'kariera'
    pageTitle = 'Kariera'

    if 'job' in request.args:
        job_id = request.args.get('job')
        try: job_id_int = int(job_id)
        except ValueError: return redirect(url_for('kariera'))
    else:
        return redirect(url_for(f'kariera'))
    
    choiced = generator_job_offer(job_id_int)
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
        f'kariera-one.html',
        pageTitle=pageTitle,
        choiced=choiced
        )

@app.route('/my-zespol')
def myZespol():
    session['page'] = 'myZespol'
    pageTitle = 'Zespół'


    if f'TEAM-ALL' not in session:
        team_list = generator_teamDB()
        session[f'TEAM-ALL'] = team_list
    else:
        team_list = session[f'TEAM-ALL']

    fullListTeam = []
    for i, member in enumerate(team_list):
       fullListTeam.append(member)
    
    return render_template(
        f'myZespol.html',
        pageTitle=pageTitle,
        
        fullListTeam=fullListTeam
        )

@app.route('/blogs')
def blogs():
    session['page'] = 'blogs'
    pageTitle = 'Blog'

    blog_post = generator_daneDBList()

    # Ustawienia paginacji
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    total = len(blog_post)
    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap4')

    # Pobierz tylko odpowiednią ilość postów na aktualnej stronie
    posts = blog_post[offset: offset + per_page]

    cats = generator_daneDBList_cetegory()
    cat_dict = cats[1]
    take_id_rec_pos = generator_daneDBList_RecentPosts(0)
    recentPosts = []
    for idp in take_id_rec_pos:
        t_post = generator_daneDBList_one_post_id(idp)[0]
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
        f'blogs.html',
        pageTitle=pageTitle,
        cat_dict=cat_dict,
        recentPosts=recentPosts,
        pagination=pagination,
        posts=posts
        )

@app.route('/blog-one', methods=['GET'])
def blogOne():
    session['page'] = 'blogOne'
    
    
    if 'post' in request.args:
        post_id = request.args.get('post')
        try: post_id_int = int(post_id)
        except ValueError: return redirect(url_for('blogs'))
    else:
        return redirect(url_for(f'blogs'))
    
    choiced = generator_daneDBList_one_post_id(post_id_int)[0]
    choiced['len'] = len(choiced['comments'])
    pageTitle = choiced['title']

    pre_next = {
        'prev': generator_daneDBList_prev_next(post_id_int)['prev'],  
        'next': generator_daneDBList_prev_next(post_id_int)['next']
        }

    cats = generator_daneDBList_cetegory()
    cat_dict = cats[1]
    take_id_rec_pos = generator_daneDBList_RecentPosts(post_id_int)
    recentPosts = []
    for idp in take_id_rec_pos:
        t_post = generator_daneDBList_one_post_id(idp)[0]
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
        f'blog.html',
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
    pageTitle = f'Wyniki wyszukiwania dla categorii {query}'

    searchResults = []
    for find_id in results:
        post_id = int(find_id[0])
        t_post = generator_daneDBList_one_post_id(post_id)[0]
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
        "searchBlog.html",
        pageTitle=pageTitle,
        posts=posts,
        found=found,
        pagination=pagination
        )


@app.route('/search-post-blog', methods=['GET', 'POST']) #, methods=['GET', 'POST']
def searchBlog():
    if request.method == "POST":
        query = request.form["query"]
        if query == '':
            print('Błąd requesta')
            return redirect(url_for('index'))
        
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
    pageTitle = f'Wyniki wyszukiwania dla {query}'

    searchResults = []
    for find_id in results:
        post_id = int(find_id[0])
        t_post = generator_daneDBList_one_post_id(post_id)[0]
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
        "searchBlog.html",
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

        zapytanie_sql = '''
                INSERT INTO contact 
                    (CLIENT_NAME, CLIENT_EMAIL, SUBJECT, MESSAGE, DONE) 
                    VALUES (%s, %s, %s, %s, %s);
                '''
        dane = (CLIENT_NAME, CLIENT_EMAIL, CLIENT_SUBJECT, CLIENT_MESSAGE, 1)
    
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
            zapytanie_sql = '''
                    INSERT INTO newsletter 
                        (CLIENT_NAME, CLIENT_EMAIL, ACTIVE, USER_HASH) 
                        VALUES (%s, %s, %s, %s);
                    '''
            dane = (SUB_NAME, SUB_EMAIL, 0, USER_HASH)
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
    pageTitle = 'subpage'

    if 'target' in request.args:
        if request.args['target'] in ['polityka', 'zasady', 'pomoc']:
            targetPage = request.args['target']
        else: targetPage = "pomoc"
    else:
        targetPage = "pomoc"

    return render_template(
        f'{targetPage}.html',
        pageTitle=pageTitle
        )



if __name__ == '__main__':
    # app.run(debug=True, port=5050)
    app.run(debug=True, host='0.0.0.0', port=5050)