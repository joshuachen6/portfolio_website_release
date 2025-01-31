import datetime
import zipfile

import flask
import os

import util
from util import DataBase
from bs4 import BeautifulSoup
import json
from auth.auth import require_auth


blueprint = flask.Blueprint(
    'editor',
    __name__,
    template_folder='templates',
    url_prefix='/editor',
    static_folder='static'
)


@blueprint.route('/', methods=['GET'])
@require_auth
def editor():
    article_id = flask.request.args['article_id']
    title, date = 'Untitled Article', datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d')
    tags, content = '', ''
    visible = 0
    icon = flask.url_for('static', filename='images/placeholder.bmp')

    database = DataBase()
    if article_id == 'new':
        # create a new article
        database.cursor.execute(
            """
            INSERT INTO articles(title, date, content, icon, visible)
            VALUES(?, ?, ?, ?, ?);
            """,
            (title, date, content, icon, visible)
        )
        database.connection.commit()
        article_id = database.cursor.lastrowid
        return flask.redirect(f'/editor?article_id={article_id}')
    else:
        database.cursor.execute(
            """
            SELECT tags.name FROM tag_list 
            JOIN tags 
            ON tags.id = tag_list.tag_id 
            WHERE tag_list.article_id = ?;
            """,
            (article_id,)
        )
        tags = database.cursor.fetchall()
        database.cursor.execute(
            """
            SELECT title, date, content, icon, visible FROM articles 
            WHERE id = ?;
            """,
            (article_id,)
        )
        result = database.cursor.fetchone()
        title, date, content, icon, visible = result

    soup = BeautifulSoup(content, 'html.parser')
    for image in soup.find_all('img'):
        image_data = {'imageSrc': image['src']}
        if image.has_attr('data-image'):
            image_data['image'] = image['data-image']
        if image.has_attr('data-video'):
            image_data['video'] = image['data-video']
        if image.has_attr('style'):
            image_data['style'] = image['style']
        image['src'] = json.dumps(image_data)

    return flask.render_template(
        'article_editor.html',
        title=title,
        date=date,
        tags=','.join([tag[0] for tag in tags]),
        content=soup.prettify(),
        icon=icon,
        visible=visible
    )


@blueprint.route('/', methods=['DELETE'])
@require_auth
def delete():
    article_id = flask.request.args['article_id']
    database = DataBase()
    database.cursor.execute(
        """
        DELETE FROM articles
        WHERE id = ?;
        """,
        (article_id,)
    )
    database.connection.commit()
    return flask.make_response('', 200)


@blueprint.route('/', methods=['PUT'])
@require_auth
def save():
    article_id = flask.request.args['article_id']

    database = DataBase()

    database.cursor.execute(
        """
        SELECT icon FROM articles
        WHERE id = ?;
        """,
        (article_id,)
    )
    icon_path = util.to_path(database.cursor.fetchone()[0])

    data = json.loads(flask.request.form.get('json'))

    # soup of the current content
    soup = BeautifulSoup(data['content'], 'html.parser')

    # gets the directory of the article
    path = os.path.join('static', 'uploads', article_id)
    os.makedirs(path, exist_ok=True)

    # set the icon
    if 'icon' in data:
        icon_path = os.path.join('', path, util.to_path(data['icon']))

    # removes all javascript for sanitation
    for script in soup.find_all('script'):
        script.decompose()

    # check if the files are still present
    current_embeds = []
    for image in soup.find_all('img'):
        current_embeds.append(util.to_path(image['data-image']))
        if image.has_attr('data-video'):
            current_embeds.append(util.to_path(image['data-video']))
        if image['data-image'] in flask.request.files:
            image['src'] = util.to_url(os.path.join('', path, util.to_path(image['data-image'])))

    # removes the file if not present
    for file in os.listdir(path):
        if file not in current_embeds and file != os.path.basename(icon_path):
            os.remove(os.path.join(path, file))

    # download the files
    if 'zip' in flask.request.files:
        zip_file = flask.request.files['zip']
        zip_path = os.path.join(path, 'data.zip')
        zip_file.save(zip_path)
        with zipfile.ZipFile(zip_path) as zipped:
            zipped.extractall(path)
        os.remove(os.path.join(zip_path))

    database.cursor.execute(
        """
        UPDATE articles
        SET title = ?,
            content = ?,
            date = ?,
            icon = ?,
            visible = ?
        WHERE id = ?;
        """,
        (data['title'], soup.prettify(), data['date'], util.to_url(icon_path), data['visibility'], article_id)
    )

    # deletes tag_links not referenced
    tags = data['tags'].split(',')
    database.cursor.execute(
        f"""
        DELETE FROM tag_list
        WHERE article_id = ?
        AND tag_id NOT IN ({','.join(['?'] * len(tags))});
        """,
        (article_id, *tags)
    )

    for term in tags:
        tag = term.strip().lower()
        # check if tag already exists
        database.cursor.execute(
            """
            SELECT * FROM tags
            WHERE name = ?;
            """,
            (tag,)
        )
        if database.cursor.fetchone() is None:
            # adds the tag
            database.cursor.execute(
                """
                INSERT INTO tags(name)
                VALUES(?);
                """,
                (tag,)
            )

        # get the id of the tag
        database.cursor.execute(
            """
            SELECT id FROM tags
            WHERE name = ?;
            """,
            (tag,)
        )
        tag_id = database.cursor.fetchone()[0]

        # check if the joining entry exists
        database.cursor.execute(
            """
            SELECT * FROM tag_list
            WHERE article_id = ? AND tag_id = ?;
            """,
            (article_id, tag_id)
        )
        if database.cursor.fetchone() is None:
            # adds the joining entry
            database.cursor.execute(
                """
                INSERT INTO tag_list(article_id, tag_id)
                VALUES(?, ?);
                """,
                (article_id, tag_id)
            )

    database.connection.commit()
    return flask.make_response('', 200)
