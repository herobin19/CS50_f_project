CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    username TEXT NOT NULL,
    hash TEXT NOT NULL
);

CREATE TABLE creams (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    cream TEXT NOT NULL,
    official_name TEXT,
    brand TEXT,
    user_id INTEGER NOT NULL
);

CREATE TABLE area(
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    area TEXT NOT NULL,
    cream_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    scheduall_id INTEGER NOT NULL,
    starting_day INTEGER,
    checker INTEGER NOT NULL,
    checktime TEXT
);

CREATE TABLE scheduall(
    id INTEGER PRIMARY KEY NOT NULL,
    scheduall TEXT
);

INSERT INTO scheduall (id, scheduall)
VALUES
(0, 'not'),
(1, 'twice a day'),
(2, 'daily'),
(3, 'once a week');