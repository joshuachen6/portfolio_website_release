import uuid

import flask

import auth.auth
from util import DataBase
import time

blueprint = flask.Blueprint(
    "api",
    __name__,
    template_folder="templates",
    url_prefix="/api",
    static_folder="static",
)


@blueprint.route("uuid")
def get_uuid():
    return flask.jsonify({"uuid": uuid.uuid4()})


@blueprint.route("/article/<article_id>")
def api_by_article_id(article_id):
    database = DataBase()

    database.cursor.execute(
        """
        SELECT title, date, content, icon, visible FROM articles 
        WHERE id = ?;
        """,
        (article_id,),
    )
    article_data = database.cursor.fetchone()
    title, date, content, icon, visible = article_data

    if not auth.auth.can_view(visible):
        return flask.make_response("", 403)

    database.cursor.execute(
        """
        SELECT tags.id FROM tag_list 
        JOIN tags 
        ON tags.id = tag_list.tag_id 
        WHERE tag_list.article_id = ?;
        """,
        (article_id,),
    )
    tags = database.cursor.fetchall()

    return flask.jsonify(
        {
            "title": title,
            "date": date,
            "body": content,
            "tags": [tag[0] for tag in tags],
            "icon": icon,
        }
    )


@blueprint.route("/tags")
def api_tags():
    database = DataBase()
    database.cursor.execute(
        """
        SELECT DISTINCT tags.id, name FROM tags
        JOIN tag_list
        ON tags.id = tag_list.tag_id
        JOIN articles
        ON tag_list.article_id = articles.id
        WHERE visible >= ?;
        """,
        (auth.auth.visibility(),),
    )
    result = database.cursor.fetchall()
    return flask.jsonify(
        {"tags": [{"id": tag_id, "name": name} for tag_id, name in result]}
    )


@blueprint.route("/browse")
def api_by_tag():
    tag = flask.request.args.get("tag")
    database = DataBase()
    visible = auth.auth.visibility()
    if "start" in flask.request.args and "size" in flask.request.args:
        start = int(flask.request.args.get("start"))
        size = int(flask.request.args.get("size"))

        database.cursor.execute(
            f"""
            SELECT DISTINCT articles.id FROM articles 
            JOIN tag_list 
                ON articles.id = tag_list.article_id 
            JOIN tags 
                ON tags.id = tag_list.tag_id 
            WHERE tags.id = ?
            AND visible >= ?
            LIMIT ? OFFSET ?;
            """,
            (tag, visible, size, start - 1),
        )
        result = database.cursor.fetchall()
        return flask.jsonify({"articles": [item[0] for item in result]})
    else:
        database.cursor.execute(
            f"""
            SELECT COUNT(DISTINCT articles.id) FROM articles 
            JOIN tag_list 
                ON articles.id = tag_list.article_id 
            JOIN tags 
                ON tags.id = tag_list.tag_id 
            WHERE tags.id = ?
            AND visible >= ?;
            """,
            (tag, visible),
        )
        result = database.cursor.fetchone()
        return flask.jsonify({"articles": result[0]})


@blueprint.route("/comments/<article>", methods=["GET", "POST"])
def api_comments(article):
    database = DataBase()
    database.cursor.execute(
        """
        SELECT visible FROM articles
        WHERE id = ?
        """,
        (article,),
    )

    visibility = database.cursor.fetchone()[0]

    if not auth.auth.can_view(visibility):
        return flask.make_response("", 403)

    if flask.request.method == "GET":
        database.cursor.execute(
            """
            SELECT COUNT(*) FROM comments 
            WHERE article_id = ?;
            """,
            (article,),
        )
        count = database.cursor.fetchone()[0]
        if count > 0:
            args = flask.request.args
            if len(args):
                start = int(args.get("start"))
                database.cursor.execute(
                    """
                    SELECT author, message, timestamp, official FROM comments 
                    WHERE article_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT 10 OFFSET ?;
                    """,
                    (article, start - 1),
                )
                output = database.cursor.fetchall()
                return flask.jsonify(
                    {
                        "comments": [
                            {
                                "author": entry[0],
                                "message": entry[1],
                                "time": entry[2],
                                "official": entry[3],
                            }
                            for entry in output
                        ]
                    }
                )
            else:
                return flask.jsonify({"size": count})
    elif flask.request.method == "POST":
        data = flask.request.json
        official = int(auth.auth.validate_auth())
        database.cursor.execute(
            """
            INSERT INTO comments (article_id, author, message, timestamp, official) 
            VALUES(?, ?, ?, ?, ?);
            """,
            (article, data["author"], data["message"], time.time_ns(), official),
        )
        database.connection.commit()

    return flask.make_response("", 200)
