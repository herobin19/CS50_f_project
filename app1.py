import os
import re
import ast

from sqlalchemy import create_engine, text 
from datetime import datetime, timedelta
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# Setting global Variables
# Reset time is the time where you can apply cream again
RESET_TIME = 3
# the time difference between the cream should be applied again for the different schedualls
RESET_DIFF = [0, 5, 12, 84]


# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Establishing connection to the database
engine = create_engine("sqlite:///cream.db", echo=True)

# Ensures data is not cached (copied from finance)
@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


#Adapted from finance
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # Query database for username
        with engine.connect() as conn:
            rows = conn.execute(text("SELECT * FROM users WHERE username = :username"), {"username": request.form.get("username")})
        rows = rows.all()
        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0][2], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0][0]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")
    

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # Ensure username does not already exist
        # checking if username is in database --> if it is len is not 0
        with engine.connect() as conn:
            rows = conn.execute(text("SELECT * FROM users WHERE username = :username"), {"username": request.form.get("username")})
        rows = rows.all()
        if (len(rows) != 0):
            return apology("username already exists")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # Ensure conformation password is the same
        elif not request.form.get("password") == request.form.get("confirmation"):
            return apology("passwords do not match")
        
        # Ensure password is safe
        elif (len(request.form.get("password")) <= 8):
            return apology("password must contain at least 8 digits, 1 lowercase letter, 1 uppercase letter and 1 number")
        elif not bool(re.search(r'\d', request.form.get("password"))):
            return apology("password must contain at least 8 digits, 1 lowercase letter, 1 uppercase letter and 1 number")
        elif not bool(re.search(r'[a-z]', request.form.get("password"))):
            return apology("password must contain at least 8 digits, 1 lowercase letter, 1 uppercase letter and 1 number")
        elif not bool(re.search(r'[A-Z]', request.form.get("password"))):
            return apology("password must contain at least 8 digits, 1 lowercase letter, 1 uppercase letter and 1 number")

        else:
            with engine.begin() as conn:
                conn.execute(
                text("INSERT INTO users (username, hash) VALUES (:username, :hash)"),
                [{"username": request.form.get("username"), "hash": generate_password_hash(request.form.get("password"))}],
                )
                conn.commit()
            return render_template("login.html")
    else:
        return render_template("register.html")


@app.route("/creams", methods=["GET", "POST"])
@login_required
def creams():
    """Add creams"""
    if request.method == "POST" and not request.form.get("delete"):
        # getting the information
        cream = request.form.get("name")
        # checking if a name was added
        if len(cream) <= 0:
            return apology("Must provide name of the cream")
        
        # checking if user already used this name for a creme
        with engine.connect() as conn:
            rows = conn.execute(text("SELECT * FROM creams WHERE cream = :cream AND user_id = :user_id "), {"cream": cream, "user_id": session["user_id"]})
        rows = rows.all()
        if (len(rows) != 0):
            return apology("You have already a cream with this name \n Please choose another")

        # if everything is fine the data can be added to the database
        else:
            with engine.begin() as conn:
                conn.execute(
                text("INSERT INTO creams (cream, official_name, brand, user_id) VALUES (:cream, :official_name, :brand, :user_id)"),
                [{"cream": cream, "official_name": request.form.get("official_name"), "brand": request.form.get("brand"), "user_id": session["user_id"]}],
                )
                conn.commit()

            # show same page with new entries again
            with engine.connect() as conn:
                rows = conn.execute(text("SELECT cream, official_name, brand FROM creams WHERE user_id = :user_id "), {"user_id": session["user_id"]})
            rows = rows.all()
            return render_template("creams.html", creams=rows)
    
    # path for deleting creams
    elif request.method == "POST":
        # deletes history and area and cream for everything for that specific cream
        cream = request.form.get("delete")
        with engine.connect() as conn:
            creams = conn.execute(text("SELECT cream FROM creams WHERE user_id = :user_id"), 
                                  {"user_id":session["user_id"]})
        creams = creams.all()
        creams_list = [item for tup in creams for item in tup]

        if cream not in creams_list:
            return apology("Please don't change the HTML")
        
        with engine.connect() as conn:
            cream_id = conn.execute(text("SELECT id FROM creams WHERE cream = :cream AND user_id = :user_id"),
                         {"cream":cream, "user_id":session["user_id"]})
            cream_id = cream_id.all()[0][0]
            conn.execute(text("DELETE FROM history WHERE area_id IN (SELECT id FROM area WHERE cream_id = :cream_id)"),
                         {"cream_id":cream_id})
            conn.execute(text("DELETE FROM area WHERE cream_id = :cream_id"),
                         {"cream_id":cream_id})
            conn.execute(text("DELETE FROM creams WHERE id = :cream_id"),
                         {"cream_id":cream_id})
            conn.commit()
        

        with engine.connect() as conn:
            rows = conn.execute(text("SELECT cream, official_name, brand FROM creams WHERE user_id = :user_id "), {"user_id": session["user_id"]})
        rows = rows.all()
        return render_template("creams.html", creams=rows)

    else:
        with engine.connect() as conn:
            rows = conn.execute(text("SELECT cream, official_name, brand FROM creams WHERE user_id = :user_id "), {"user_id": session["user_id"]})
        rows = rows.all()
        return render_template("creams.html", creams=rows)
    

@app.route("/areas", methods=["GET", "POST"])
@login_required
def areas():
    """Adding the areas where to put the creams"""
    # Getting data from databases that is needed for both ways
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT cream FROM creams WHERE user_id = :user_id "), {"user_id": session["user_id"]})
        scheduall = conn.execute(text("SELECT * FROM scheduall"))
    creams = rows.all()
    creams_list = [item for tup in creams for item in tup]
    schedualls = scheduall.all()
    def return_areas():
        """Getting Information of the areas out of the database"""
        with engine.connect() as conn:
            area_info = conn.execute(text("SELECT area, cream, scheduall, starting_day FROM area JOIN creams ON area.cream_id = creams.id JOIN scheduall ON area.scheduall_id = scheduall.id WHERE area.user_id = :user_id"), {"user_id": session["user_id"]})
        area_info = area_info.all()
        return render_template("areas.html", areas=area_info, creams=creams, scheduall=schedualls)


    if request.method == "POST" and not request.form.get("delete"):
        # Ensure user typed in an area 
        area = request.form.get("area")
        if len(area) <= 0:
            return apology("Must provide name of the skin area")
        
        # Ensure user has not changed HTML for creams
        cream = request.form.get("cream")
        if not cream in creams_list:
            return apology("Cream need to be part of your creams")
        
        # Ensure user has not changed HTML for day
        day = request.form.get("day")
        try:
            day = int(day)
            if day < 1 or day > 7:
                return apology("Please don't change the HTML")
        except:
            return apology("Please don't change the HTML")
        
        # Ensure user has not changed HTML for creams
        scheduall = request.form.get("scheduall")
        try:
            scheduall = int(scheduall)
            if scheduall < 0 or scheduall > len(schedualls) - 1:
                return apology("Please don't change the HTML")
            elif scheduall < 3:
                day = None
        except:
            return apology("Please don't change the HTML")

        # If user puts same area with the same cream in twice it should not be added. but the scheduall will be updated
        with engine.connect() as conn:
            double = conn.execute(text("SELECT id FROM area WHERE user_id = :user_id AND area = :area AND cream_id = (SELECT id FROM creams WHERE cream = :cream AND user_id = :user_id)"), {"user_id": session["user_id"], "area": area, "cream": cream}) 
            double = double.all()
        if len(double) > 0:
            with engine.begin() as conn:
                conn.execute(
                text("UPDATE area SET scheduall_id = :scheduall_id WHERE id = :id"),
                {"scheduall_id": scheduall, "id" : double[0][0]},
                )
                conn.commit()
            return return_areas()
            
            
        # if everything is fine it can be added to the database
        with engine.begin() as conn:
            conn.execute(
            text("INSERT INTO area (area, cream_id, user_id, scheduall_id, starting_day, checker, checktime) VALUES (:area, (SELECT id FROM creams WHERE cream = :cream AND user_id = :user_id), :user_id, :scheduall_id, :starting_day, 0, :checktime)"),
            [{"area": area, "cream": cream, "user_id": session["user_id"], "scheduall_id": scheduall, "starting_day": day, "checktime": datetime.now()}],
            )
            conn.commit()
        
        return return_areas()
    
    # for deletion
    if request.method == "POST" and request.form.get("delete"):
        area = request.form.get("delete")
        # turning input string back to a tuple
        try:
            area = ast.literal_eval(area)
        except:
            return apology("Please don't change the html")
        # Ensure html was not changed and area and cream are both in the lists
        with engine.connect() as conn:
            areas = conn.execute(text("SELECT area FROM area WHERE user_id = :user_id "), {"user_id": session["user_id"]})
        areas = areas.all()
        areas_list = [item for tup in areas for item in tup]
        if area[0] not in areas_list or area[1] not in creams_list:
            return apology("Please don't change the html")
        
        # Deleting area and history entries
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM history WHERE area_id = (SELECT id FROM area WHERE area = :area AND cream_id = (SELECT id FROM creams WHERE cream = :cream AND user_id = :user_id))"),
                [{"area": area[0], "cream": area[1], "user_id": session["user_id"]}],
            )
            conn.execute(text("DELETE FROM area WHERE area = :area AND cream_id = (SELECT id FROM creams WHERE cream = :cream and user_id = :user_id)"),
                [{"area": area[0], "cream": area[1], "user_id": session["user_id"]}],
            )
            conn.commit()
        return return_areas()
    else:
        # Putting in the cream names into the html
        return return_areas()


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    # Getting a List of all the creams of the user that are in use
    def remind():
        with engine.connect() as conn:
            creams = conn.execute(text("SELECT cream FROM creams WHERE user_id = :user_id AND id IN (SELECT cream_id FROM area WHERE user_id = :user_id AND NOT scheduall_id = 0 AND checker = 0)"), {"user_id": session["user_id"]}) 
        creams = creams.all()
        creams = [item for tup in creams for item in tup]

        # Making a dictionary with the creams and the corresponding areas
        reminder = {}
        for cream in creams:
            with engine.connect() as conn:
                areas = conn.execute(text("SELECT area FROM area WHERE cream_id = (SELECT id FROM creams WHERE cream = :cream AND user_id = :user_id AND NOT scheduall_id = 0 AND checker = 0)"),
                                    {"user_id": session["user_id"], "cream":cream})
            areas = areas.all()
            areas = [item for tup in areas for item in tup]
            reminder[cream] = areas
        return reminder
    

    # Uncheckes areas that where cream need to be applied again
    def reset_checker():
        """Uncheckes area where the checktime is before now"""
        now = datetime.now()
        # getting all the areas from the user and looping through them
        with engine.connect() as conn:
            areas = conn.execute(text("SELECT id, checktime, scheduall_id FROM area WHERE user_id = :user_id AND checker = 1 AND NOT scheduall_id = 0"),
            {"user_id": session["user_id"]})
        areas = areas.all()
        for area in areas:
            # checking if area needs to be creamed again
            checktime = datetime.strptime(area[1][0:19], '%Y-%m-%d %H:%M:%S')
            scheduall = area[2]
            if checktime < now:
                with engine.begin() as conn:
                    conn.execute(
                        text("UPDATE area SET checker = 0 WHERE id = :id"),
                        [{"id": area[0]}],
                    )
                    conn.commit()
                
    def add_forgotten():
        """uptdates history for times where it was forgotten to use creams"""
        with engine.begin() as conn:
            areas = conn.execute(
                text("SELECT id, scheduall_id, checktime, starting_day FROM area WHERE user_id = :user_id AND NOT scheduall_id = 0 AND checker = 0"),
                [{"user_id": session["user_id"]}]
            )
        areas = areas.all()
        now = datetime.now()
        for area in areas:
            checktime = datetime.strptime(area[2][0:19], '%Y-%m-%d %H:%M:%S')
            scheduall = area[1]
            starting_day = area[3]
            timeframes = [timedelta(hours=0), timedelta(hours=12), timedelta(hours=24), timedelta(days=7)]
            # checking how often cream was not applied
            ## setting checktime at the start/end of a cream timeframe
            if scheduall == 1:
                if checktime.hour < RESET_TIME:
                    checktime = checktime.replace(minute=0, hour=RESET_TIME + 12)
                    checktime = checktime - timedelta(days=1)
                elif checktime.hour < RESET_TIME + 12:
                    checktime = checktime.replace(minute=0, hour=RESET_TIME)
                else:
                    checktime = checktime.replace(minute=0, hour=RESET_TIME + 12)
            elif scheduall == 2:
                if checktime.hour < RESET_TIME:
                    checktime = checktime.replace(minute=0, hour=RESET_TIME)
                    checktime = checktime - timedelta(days=1)
                else:
                    checktime = checktime.replace(minute=0, hour=RESET_TIME)
            elif scheduall == 3:
                weekday = now.isoweekday()
                if checktime.hour < RESET_TIME:
                    if weekday > starting_day:
                        checktime = checktime.replace(second=0, minute=0, hour=RESET_TIME)
                        checktime = checktime - timedelta(days=(weekday-starting_day))
                    else:
                        checktime = checktime.replace(second=0, minute=0, hour=RESET_TIME)
                        checktime = checktime - timedelta(days=7-(starting_day-weekday))
                else:
                    if weekday >= starting_day:
                        checktime = checktime.replace(second=0, minute=0, hour=RESET_TIME)
                        checktime = checktime - timedelta(days=(weekday-starting_day))
                    else:
                        checktime = now.replace(second=0, minute=0, hour=RESET_TIME)
                        checktime = checktime - timedelta(days=7-(starting_day-weekday))
            # checking and adding enties until it is now
            while checktime < now - timeframes[scheduall]:
                with engine.begin() as conn:
                    checktime = checktime + timeframes[scheduall]
                    conn.execute(
                        text("UPDATE area SET checktime = :checktime  WHERE id = :id"),
                        [{"id": area[0], "checktime":checktime}],
                    )
                    conn.execute(
                        text("INSERT INTO history (area_id, cream_time, applied) VALUES (:area_id, :cream_time, 0)"),
                        [{"area_id": area[0], "cream_time": checktime}]
                    )
                    conn.commit()
                    

                
                    
    def next_time(area_id):
        """Calculates the next time where cream can be applied"""
        now = datetime.now()
        with engine.begin() as conn:
            scheduall = conn.execute(
            text("SELECT scheduall_id FROM area WHERE id = :id"),
            [{"id": area_id}],
            )
        scheduall = scheduall.all()[0][0]
        # For twice a day scheduall
        if scheduall == 1:
            if now.hour < RESET_TIME:
                new_time = now.replace(minute=0, hour=RESET_TIME)
            elif now.hour < RESET_TIME + 12:
                new_time = now.replace(minute=0, hour=RESET_TIME + 12)
            else:
                new_time = now.replace(minute=0, hour=RESET_TIME)
                new_time = new_time + timedelta(days=1)
            if new_time < (now + timedelta(hours=RESET_DIFF[scheduall])):
                new_time = now + timedelta(hours=RESET_DIFF[scheduall])
            

        # For daily scheduall
        elif scheduall == 2:
            if now.hour < RESET_TIME:
                new_time = now.replace(minute=0, hour=RESET_TIME)
            else:
                new_time = now.replace(minute=0, hour=RESET_TIME)
                new_time = new_time + timedelta(days=1)
            if new_time < (now + timedelta(hours=RESET_DIFF[scheduall])):
                new_time = now + timedelta(hours=RESET_DIFF[scheduall])
        
        # For weekly scheduall
        elif scheduall == 3:
            with engine.begin() as conn:
                starting_day = conn.execute(
                text("SELECT starting_day FROM area WHERE id = :id"),
                [{"id": area_id}],
                )
            starting_day = starting_day.all()[0][0]
            weekday = now.isoweekday()
            if now.hour < RESET_TIME:
                if weekday > starting_day:
                    new_time = now.replace(second=0, minute=0, hour=RESET_TIME)
                    new_time = new_time + timedelta(days=(7 - (weekday-starting_day)))
                else:
                    new_time = now.replace(second=0, minute=0, hour=RESET_TIME)
                    new_time = new_time + timedelta(days=(starting_day-weekday))
            else:
                if weekday >= starting_day:
                    new_time = now.replace(second=0, minute=0, hour=RESET_TIME)
                    new_time = new_time + timedelta(days=(7 - (weekday-starting_day)))
                else:
                    new_time = now.replace(second=0, minute=0, hour=RESET_TIME)
                    new_time = new_time + timedelta(days=(starting_day-weekday))
            if new_time < (now + timedelta(hours=RESET_DIFF[scheduall])):
                new_time = now + timedelta(hours=RESET_DIFF[scheduall]) 
        else:
            new_time = None

        return new_time

    reset_checker()
    reminder = remind()
    add_forgotten()
    if request.method == "POST":
        #Looping through all the different areas and checking if they were submitted
        for cream in reminder:
            for area in reminder[cream]:
                checker = request.form.get(cream+area)
                # if it was checked, checker is not Null
                if checker:
                    # calculating the next time were the cream can be applied
                    with engine.begin() as conn:
                        area_id = conn.execute(
                            text("SELECT id FROM area WHERE user_id = :user_id AND cream_id = (SELECT id FROM creams WHERE cream = :cream AND user_id = :user_id) AND area = :area"),
                            [{"area": area, "cream": cream, "user_id": session["user_id"]}],
                        )
                    area_id = area_id.all()[0][0]
                    print(area, cream, session["user_id"])
                    with engine.begin() as conn:
                        conn.execute(
                            text("UPDATE area SET checker = 1, checktime = :checktime  WHERE user_id = :user_id AND cream_id = (SELECT id FROM creams WHERE cream = :cream AND user_id = :user_id) AND area = :area"),
                            [{"area": area, "cream": cream, "user_id": session["user_id"], "checktime": next_time(area_id)}],
                        )
                        conn.execute(
                            text("INSERT INTO history (area_id, cream_time, applied) VALUES (:area_id, :cream_time, 1)"),
                            [{"area_id": area_id, "cream_time": datetime.now()}]
                        )
                        conn.commit()
        
        # reminder must be updated, because it changes when something is submitted
        return render_template("index.html", reminder=remind()) 
    
    else:
        return render_template("index.html", reminder=reminder) 


@app.route("/history", methods=["GET", "POST"])
@login_required
def history():
    """shows history"""
    with engine.begin() as conn:
        history = conn.execute(
        text("""SELECT area, cream, cream_time, applied FROM history 
                JOIN area ON history.area_id=area.id
                JOIN creams ON area.cream_id=creams.id
                WHERE area.user_id = :user_id"""),
            [{"user_id": session["user_id"]}],
        )
    
    history = history.all()[::-1]
    # getting lists of all the unique areas and creams for filter
    areas = []
    creams = []
    for element in history:
        if element[0] not in areas:
            areas.append(element[0])
        if element[1] not in creams:
            creams.append(element[1])

    if request.method == "POST":
        cream = request.form.get("cream")
        area = request.form.get("area")
        history2 = []
        # the different cases if one or more filter are left blank
        if not area and not cream:
            history2 = history
        elif not area:
            for his in history:
                if his[1] == cream:
                    history2.append(his)
        elif not cream:
            for his in history:
                if his[0] == area:
                    history2.append(his)
        else:
            for his in history:
                if his[0] == area and his[1] == cream:
                    history2.append(his)
        history = history2
        return render_template("history.html", history=history, areas=areas, creams=creams)
    else:
        return render_template("history.html", history=history, areas=areas, creams=creams)

