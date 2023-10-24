import os
import re

from sqlalchemy import create_engine, text 
from datetime import datetime
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

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

@app.route("/")
@login_required
def hello_world():
    return apology("You are in")


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
    """Add cremes"""
    if request.method == "POST":
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
            return render_template("cremes.html", cremes=rows)
        
    else:
        with engine.connect() as conn:
            rows = conn.execute(text("SELECT cream, official_name, brand FROM creams WHERE user_id = :user_id "), {"user_id": session["user_id"]})
        rows = rows.all()
        return render_template("cremes.html", creams=rows)
    

@app.route("/areas", methods=["GET", "POST"])
@login_required
def areas():
    # Getting data from databases that is needed for both ways
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT cream FROM creams WHERE user_id = :user_id "), {"user_id": session["user_id"]})
        scheduall = conn.execute(text("SELECT * FROM scheduall"))
    creams = rows.all()
    schedualls = scheduall.all()
    if request.method == "POST":
        # Ensure user typed in an area 
        area = request.form.get("area")
        if len(area) <= 0:
            return apology("Must provide name of the skin area")
        
        # Ensure user has not changed HTML for creams
        cream = request.form.get("cream")
        creams_list = [item for tup in creams for item in tup]
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

        # Ensure user did not input the same area with the same cream twice
        with engine.connect() as conn:
            test = conn.execute(text("SELECT * FROM area WHERE user_id = :user_id AND area = :area AND cream_id = (SELECT id FROM creams WHERE cream = :cream AND user_id = :user_id)"), {"user_id": session["user_id"], "area": area, "cream": cream}) 
            test = test.all()
        if len(test) > 0:
            return apology("Entry already exists")
        # if everything is fine it can be added to the database
        with engine.begin() as conn:
                conn.execute(
                text("INSERT INTO area (area, cream_id, user_id, scheduall_id, starting_day) VALUES (:area, (SELECT id FROM creams WHERE cream = :cream AND user_id = :user_id), :user_id, :scheduall_id, :starting_day)"),
                [{"area": area, "cream": cream, "user_id": session["user_id"], "scheduall_id": scheduall, "starting_day": day}],
                )
                conn.commit()
        
        return render_template("areas.html", creams=creams, scheduall=schedualls)
        


    else:
        # Putting in the cream names into the html
        return render_template("areas.html", creams=creams, scheduall=schedualls)

    

