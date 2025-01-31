import flask
from bs4 import BeautifulSoup
import os

import auth.auth
from util import DataBase

blueprint = flask.Blueprint(
    "article",
    __name__,
    template_folder="templates",
    url_prefix="/article",
    static_folder="static",
)


def generate_tag_links(tags):
    return ", ".join(
        [
            f'<a href="/article/browse#{tag_id}">{tag_name}</a>'
            for tag_name, tag_id in tags
        ]
    )


@blueprint.route("/<article_id>")
def articles(article_id):
    database = DataBase()
    database.cursor.execute(
        """
        SELECT tags.name, tags.id FROM tag_list 
        JOIN tags 
        ON tags.id = tag_list.tag_id 
        WHERE tag_list.article_id = ?;
        """,
        (article_id,),
    )
    tags = database.cursor.fetchall()
    database.cursor.execute(
        """
        SELECT title, content, date FROM articles 
        WHERE id = ?
        AND visible >= ?;
        """,
        (article_id, auth.auth.visibility()),
    )
    result = database.cursor.fetchone()
    if result is not None:
        title, content, date = result
        soup = BeautifulSoup(content, "html.parser")
        # parse through and replace the thumbnails with the videos
        for image in soup.find_all("img"):
            image["style"] = f"height: auto; width: {image['data-width']};"
            image["width"] = ""
            if image.has_attr("data-video"):
                video = soup.new_tag("video")
                video["controls"] = ""
                path = os.path.join("static", "uploads", article_id)
                video["src"] = "/".join(["", path, image["data-video"]])
                if image.has_attr("style"):
                    video["style"] = image["style"]
                image.replace_with(video)

        content = soup.prettify()
        return flask.render_template(
            "article_base.html",
            blog_title=title,
            blog_tags=f"<h4>Topics: {generate_tag_links(tags)}</h4>"
            if (len(tags) > 1 or tags[0][0] != "")
            else "",
            blog_body=content,
            blog_date=f"<p>Date: {date}</p>" if date.strip() != "" else "",
            editor_link=f"/editor?article_id={article_id}",
        )
    return flask.redirect("/article/index")


def generate_decks():
    database = DataBase()
    database.cursor.execute(
        """
        SELECT DISTINCT tags.id, tags.name FROM tags
        JOIN tag_list
        ON tags.id = tag_list.tag_id
        JOIN articles
        ON tag_list.article_id = articles.id
        WHERE visible >= ?;
        """,
        (auth.auth.visibility(),),
    )
    tags = database.cursor.fetchall()
    html = []
    for tag_id, tag_name in tags:
        html.append(
            f"""
            <div class="deck-container row hidden fade">
                <h3>{tag_name}</h3>
                <div class="col-auto d-flex justify-content-center align-items-center">
                    <button class="left button">
                        <span class="material-icons icon-m">west</span>
                    </button>
                </div>
                <div class="card-deck col d-flex justify-content-center" id="{tag_id}">
    
                </div>
                <div class="col-auto d-flex justify-content-center align-items-center">
                    <button class="right button">
                        <span class="material-icons icon-m">east</span>
                    </button>
                </div>
                <hr class="border-2 mt-5 mb-5 rounded">
            </div>
            """
        )
    return "".join(html)


@blueprint.route("/browse")
def browse():
    return flask.render_template("browse.html", decks=generate_decks())


def create_table():
    database = DataBase()
    database.cursor.execute(
        """
        SELECT title, date, id, visible
        FROM articles
        """,
    )
    articles = database.cursor.fetchall()
    html = ""
    for i in range(len(articles)):
        article = articles[i]
        title, date, id, visible = article
        if auth.auth.can_view(visible):
            html += f"""
            <tr onclick="window.location.href = '/article/{id}';" class="clickable {'' if visible else 'strike'}">
                <td>{i + 1}</td>
                <td>{title}</td>
                <td>{date}</td>
            </tr>
            """
    return html


@blueprint.route("/index")
def index():
    return flask.render_template("index.html", table=create_table())
