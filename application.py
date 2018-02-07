from flask import Flask, url_for, request, render_template, session, redirect, flash
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, and_, update

from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp
import os
import random
from functions import *

# Create application instance
app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["PREFERRED_URL_SCHEME"] = 'https'
app.config["DEBUG"] = True
Session(app)

# store refernece to python functions required in jinja
app.jinja_env.globals.update(enumerate=enumerate, str=str)

# Flask-SQLAlchemy
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ['DATABASE_URL']
app.config["SQLALCHEMY_ECHO"] = True
db = SQLAlchemy(app)

# Adopter database tables
class User(db.Model):

    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text)
    email = db.Column(db.Text)
    hash = db.Column(db.Text)

    def __init__(self, username, email, hash):
        self.username = username
        self.email = email
        self.hash = hash

class Trait(db.Model):

    __tablename__ = "traits"
    id = db.Column(db.Integer, primary_key=True)
    trait = db.Column(db.Text)

    def __init__(self, trait):
        self.trait = trait

class Preference(db.Model):

    __tablename__ = "preferences"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    trait_id = db.Column(db.Integer, db.ForeignKey('traits.id'))

    def __init__(self, user_id, trait_id):
        self.user_id = user_id
        self.trait_id = trait_id

class Type(db.Model):

    __tablename__ = "type"
    id = db.Column(db.Integer, primary_key=True)
    species = db.Column(db.Text)

    def __init__(self, species):
        self.species = species

class Animal(db.Model):

    __tablename__ = "animals"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    type_id = db.Column(db.Integer, db.ForeignKey('type.id'))
    age = db.Column(db.Text)
    breed = db.Column(db.Text)
    description = db.Column(db.Text)
    shelter_id = db.Column(db.Integer, db.ForeignKey('shelters.id'))

    def __init__(self, name, type_id, age, breed, description, shelter_id):
        self.name = name
        self.type_id = type_id
        self.age = age
        self.breed = breed
        self.description = description
        self.shelter = shelter

class Animal_Profile(db.Model):

    __tablename__ = "animal_profile"
    id = db.Column(db.Integer, primary_key=True)
    trait_id = db.Column(db.Integer, db.ForeignKey('traits.id'))

    def __init__(self, trait_id):
        self.trait_id = trait_id

class Shelter(db.Model):

    __tablename__ = "shelters"
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.Text)
    phone = db.Column(db.Text)

    def __init__(self, address, phone):
        self.address = address
        self.phone = phone

class Swipe(db.Model):

    __tablename__ = "swipes"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    animal_id = db.Column(db.Integer)
    match = db.Column(db.Boolean)

    def __init__(self, user_id, animal_id, match):
        self.user_id = user_id
        self.animal_id = animal_id
        self.match = match

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    # if user selects matches button
    if request.method == 'POST':
        return redirect(url_for('preferences'))
    # else if user reached route via GET
    else:
        return render_template('index.html')

@app.route('/preferences', methods=['GET', 'POST'])
@login_required
def preferences():
    # pull users saved preferences
    preferences = Preferences.query.filter(Preferences.user_id == session["user_id"])
    current = preferences.first()

    # if the user clicks button to save preferences and show matches
    if request.method == 'POST':
        #save preferences to db
        personality = request.form.getlist("check")

        checkboxes = {"dog": 0, "cat": 0, "young": 0, "adult": 0, "senior": 0, "small": 0,
            "medium": 0, "large": 0, "active": 0, "kids": 0, "animals": 0, "special": 0}

        for trait in personality:
            if trait in checkboxes.keys():
                checkboxes[trait] = 1

        if current == None:
            # create new preferences object for user
            preferences = Preferences(session['user_id'], checkboxes["dog"], checkboxes["cat"],
                checkboxes["young"], checkboxes["adult"], checkboxes["senior"], checkboxes["small"],
                checkboxes["medium"], checkboxes["large"], checkboxes["active"], checkboxes["kids"],
                checkboxes["animals"], checkboxes["special"])
            db.session.add(preferences)
        else:
            # update users current preferences
            preferences.update(checkboxes)

        db.session.flush()
        db.session.commit()
        return redirect(url_for('match'))

    else:
        if current == None:
            current = {}
        else:
            current = current.__dict__

        return render_template('preferences.html', preferences=current)

@app.route('/match')
@login_required
def match():
    #pull user preferences from db
    pref = Preferences.query.filter(Preferences.user_id == session["user_id"]).first()

    if pref == None:
        flash("Please set preferences prior to looking for matches.")
        return redirect(url_for('preferences'))

    pref = pref.__dict__
    description = ['young', 'adult', 'senior', 'small', 'medium', 'large']
    for trait, value in pref.items():
        # if trait in description array and value is true, value updated to string
        if str(trait) in description:
            if value:
                pref[trait] = str(trait)
        if str(trait) == 'active' or str(trait) == 'special':
            if value:
                pref[trait] = [0, 1] #accept trait as true or false if selected
            else:
                pref[trait] = [0] #accept trait as only false if selected
        if str(trait) == 'kids' or str(trait) == 'animals':
            if value:
                pref[trait] = [1] #accept trait as only true if selected
            else:
                pref[trait] = [0, 1] #accept trait as true or false if selected

    # pull users matches and already viewed animals
    swipes = Swipe.query.filter(Swipe.user_id == session["user_id"]).all()

    # create list of animal ids not to be selected with query
    ids = []
    for swipe in swipes:
        ids.append(int(swipe.animal_id))
    print(ids)

    # query db for animals that match preferences
    dogs = Animal.query.filter(and_(
        Animal.dog == pref['dog'],
        or_(Animal.age == pref['young'], Animal.age == pref['adult'], Animal.age == pref['senior']),
        or_(Animal.size == pref['small'], Animal.size == pref['medium'], Animal.size == pref['large']),
        Animal.active.in_(pref['active']),
        Animal.kids.in_(pref['kids']),
        Animal.animals.in_(pref['animals']),
        Animal.special.in_(pref['special']),
        Animal.id.notin_(ids))).all()

    cats = Animal.query.filter(and_(
        Animal.cat == pref['cat'],
        or_(Animal.age == pref['young'], Animal.age == pref['adult'], Animal.age == pref['senior']),
        Animal.active.in_(pref['active']),
        Animal.kids.in_(pref['kids']),
        Animal.animals.in_(pref['animals']),
        Animal.special.in_(pref['special']),
        Animal.id.notin_(ids))).all()

    print(dogs)
    print(cats)

    animals = cats + dogs
    random.shuffle(animals)

    return render_template('match.html', animals=animals)

@app.route('/save_swipe', methods=['POST'])
def save_swipe():

    if request.method == 'POST':
        # Ensure item id parameter is present
        if not request.form.get("animal_id"):
            raise RuntimeError("missing item")

        #create swipe object and add to db
        swipe = Swipe(session['user_id'], int(request.form.get("animal_id")), int(request.form.get("match")))
        db.session.add(swipe)
        db.session.commit()

        return "swipe saved"

    else:
        return "error"

@app.route('/matches')
@login_required
def chat():
    # pull users matches from swipes table
    swipes = Swipe.query.filter(and_(Swipe.user_id == session["user_id"], Swipe.match == 1)).all()

    # create list of animal ids to be selected with query
    ids = []
    for swipe in swipes:
        ids.append(int(swipe.animal_id))

    # query animal table for ids that match positive swipes
    animals = Animal.query.filter(Animal.id.in_(ids)).all()

    return render_template('matches.html', animals=animals)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # hash password
        hash = pwd_context.hash(request.form.get("password"))

        # Check if username or email are already registered
        rows = User.query.filter(or_(User.username == request.form.get("username"), User.email == request.form.get("email"))).first()

        if rows != None:
            flash("Username and/or email already registered.")
            return redirect(url_for('register'))

        #create user object and add to db
        user = User(request.form.get("username"), request.form.get("email"), hash)
        db.session.add(user)
        db.session.flush()

        # remember which user is logged in
        session['user_id'] = user.id

        db.session.commit()
        return redirect(url_for('index'))
    else:
        return render_template('register.html')

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    if request.method == "POST":
        # query database for username
        user = User.query.filter(User.username == request.form.get("username")).first()

        # ensure username exists and password is correct
        if user == None or not pwd_context.verify(request.form.get("password"), user.hash):
            # flash message and redirect back to login page
            flash("Username and/or password is incorrect")
            return redirect(url_for("login"))

        # remember which user is logged in
        session['user_id'] = user.id

        # redirect user to home page
        return redirect(url_for("index"))
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))
