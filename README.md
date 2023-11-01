# CREAM REMINDER
#### Video DEMO: https://www.youtube.com/watch?v=m4ZO5DQOGFo
#### Description:
Cream Reminder let you insert creams and areas where to put the cream, along with a schedual (twice a day, daily, or once a week)
It shows you all the areas where you still need to cream and the creams you need to use
You can check off the area when creamed
It also creates a history with the times when you checked of, but also when you have forgotten to check of

## Web application basics
The basis of this web application is pretty much the same as for finance
Consequentially login.html, register.html, logout.html and apology.html are pretty much the same as in finance
### Register
Additional requierements for the password:
"password must contain at least 8 digits, 1 lowercase letter, 1 uppercase letter and 1 number"
### General changes
#### SQLalchemy
I didn't want to use the cs50 library, because I wanted to develope the app more like in real life.
I used SQLalchemy instead. 
This was a mistake, because I only wanted to use the normal SQL syntax so the code looks like:
```python
with engine.begin() as conn:
    conn.execute(
        text("INSERT INTO users (username, hash) VALUES (:username, :hash)"),
        [{"username": request.form.get("username"), "hash": generate_password_hash(request.form.get("password"))}],
    )
    conn.commit()
```
For select statements, this only gave me back tuples instead of dictionaries, which led to ugly coding
Better would be to use the cs50 library or sqlite3.

## Creams (creams.html)
Lets you enter the name of the cream (how the cream is referred on on the rest of the website)
and optionally the official name and the brand, so you better know which exact cream is meant by the name you geve it.
The data is stored in the table
```SQL
CREATE TABLE creams (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    cream TEXT NOT NULL,
    official_name TEXT,
    brand TEXT,
    user_id INTEGER NOT NULL
);
```
It also shows you a table where every cream of yours is listed
There you can also delete creams (but deleting also deletes every area and history entry connected with this cream)

## Areas (areas.html)
Lets you enter a area (a name of your choosing) a cream (only creams that were already registered in creams) and a scheduall (twice a day, daily, once a week or not). not is when the area is good and you don't need to cream there.
You can use different creams for the same area
You can can change the scheduall by entering the area and cream name again with a different scheduall
The data is stored in the table:
```SQL
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
```
(checker is used as boolean where "already checked"=1 and "not checked"=2)

It also shows you a table where every area is listed
There you can also delete areas (but deleting also deletes every history entry connected with this area)

## Cream Reminder (index.html)
Shows a checklist of every skin area where you still need to apply cream
You can check it off so it will not be there anymore
Any check process will be added to history
```SQL
CREATE table history(
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    area_id INTEGER NOT NULL,
    cream_time TEXT NOT NULL,
    applied INTEGER NOT NULL
);
```
(applied is used as a boolean, where 1 means cream is applied and 0 means cream was forgotten)


### Algorythmus
Every time a area is checked the next time when the cream can be applied (checktime) is safed
This is calculated with the function
```Python
def next_time(area_id):
```
#### The next time (checktime) is:
- Twice a day: at 3 or 15 o'clock
- daily: at 3 o'clock
- weekly: at 3 o'clock at the starting day, you put it
or 
- Twice a day: 5 hours
- daily: 12 hours
- weekly: 84 hours
after you checked it off
The one that is later is used

If you load the remind page again it will check if it is later than the checktime and if so it will be shown again and can be checked off again.
```Python
def reset_checker():
```

The function:
```Python
def add_forgotten():
```
checkes everytime Cream Reminder (index page) is loaded if you have forgotten a cream timeslot based on the checktime and the scheduall and adds it to history

## History (history.html)
shows the history of everytime cream was applied or forgotten
Has a filter function where you can filter which area or cream you want to see
