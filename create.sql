CREATE TABLE IF NOT EXISTS articles(
    id INTEGER PRIMARY KEY,
    title TEXT,
    content TEXT,
    date TEXT,
    icon TEXT,
    visible INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS tags(
    id INTEGER PRIMARY KEY,
    name TEXT
);

CREATE TABLE IF NOT EXISTS tag_list(
    article_id INTEGER,
    tag_id INTEGER,
    FOREIGN KEY (article_id) REFERENCES articles (id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS comments(
    id INTEGER PRIMARY KEY,
    author TEXT,
    message TEXT,
    timestamp INTEGER,
    official INTEGER DEFAULT 0,
    article_id INTEGER,
    FOREIGN KEY (article_id) REFERENCES articles (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS sessions(
    token TEXT,
    timestamp INTEGER,
    level INTEGER
);

CREATE TRIGGER IF NOT EXISTS clean_tags
AFTER DELETE ON tag_list
BEGIN
    DELETE FROM tags
    WHERE NOT EXISTS(
        SELECT 1 FROM tag_list
        WHERE tag_list.tag_id = tags.id
    );
end;

CREATE TRIGGER IF NOT EXISTS clean_tag_links
AFTER DELETE ON articles
BEGIN
    DELETE FROM tag_list
    WHERE NOT EXISTS(
        SELECT 1 FROM articles
        WHERE articles.id = tag_list.article_id
    );
end;

