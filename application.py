from flask import Flask, url_for, request, render_template, session, redirect, flash
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, and_, update
from sqlalchemy.orm import relationship

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
    name = db.Column(db.Text)

    def __init__(self, name):
        self.name = name

class Preferences(db.Model):

    __tablename__ = "preferences"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    trait_id = db.Column(db.Integer, db.ForeignKey('traits.id'))
    trait = relationship("Trait")

    def __init__(self, user_id, trait_id):
        self.user_id = user_id
        self.trait_id = trait_id

class Type(db.Model):

    __tablename__ = "type"
    id = db.Column(db.Integer, primary_key=True)
    species = db.Column(db.Text)

    def __init__(self, species):
        self.species = species

class Type_Preference(db.Model):

    __tablename__ = "type_preferences"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    type_id = db.Column(db.Integer, db.ForeignKey('type.id'))
    type = relationship("Type")

    def __init__(self, user_id, type_id):
        self.user_id = user_id
        self.type_id = type_id

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
    animal_id = db.Column(db.Integer, primary_key=True)
    trait_id = db.Column(db.Integer, db.ForeignKey('traits.id'))
    trait = relationship("Trait")

    def __init__(self, animal_id, trait_id):
        self.animal_id = animal_id
        self.trait_id = trait_id

class Shelter(db.Model):

    __tablename__ = "shelters"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    address = db.Column(db.Text)
    phone = db.Column(db.Text)

    def __init__(self, name, address, phone):
        self.name = name
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
    trait_preferences = Preferences.query.join(Trait).filter(Preferences.user_id == session["user_id"]).all()
    type_preferences = Type_Preference.query.join(Type).filter(Type_Preference.user_id == session["user_id"]).all()

    # array storing currently saved preferences from db
    current_trait_prefs = []
    current_type_prefs = []

    # if the user clicks button to save preferences and show matches
    if request.method == 'POST':
        # returns array of checked checkboxes
        selected_type = request.form.getlist("type")
        selected_traits = request.form.getlist("trait")

        # add currently saved type and trait preferences to array
        # delete from table if no longer selected
        for trait in trait_preferences:
            current_trait_prefs.append(trait.trait.name)
            if trait.trait.name not in selected_traits:
                db.session.delete(trait)

        for animal_type in type_preferences:
            current_type_prefs.append(animal_type.type.species)
            if animal_type.type.species not in selected_type:
                db.session.delete(animal_type)

        # add new type and trait preference to respective table
        for trait in selected_traits:
            if trait not in current_trait_prefs:
                new_trait = Trait.query.filter(Trait.name == trait).first()
                preference = Preferences(session['user_id'], new_trait.id)
                db.session.add(preference)

        for animal_type in selected_type:
            if animal_type not in current_type_prefs:
                species = Type.query.filter(Type.species == animal_type).first()
                type_preference = Type_Preference(session['user_id'], species.id)
                db.session.add(type_preference)

        db.session.commit()

        return redirect(url_for('match'))

    else:
        for trait in trait_preferences:
            current_trait_prefs.append(trait.trait.name)

        for type in type_preferences:
            current_type_prefs.append(type.type.species)

        return render_template('preferences.html', type_preferences=current_type_prefs, trait_preferences=current_trait_prefs)

@app.route('/match')
@login_required
def match():
    #pull user preferences from db
    trait_preferences = Preferences.query.join(Trait).filter(Preferences.user_id == session["user_id"]).all()
    type_preferences = Type_Preference.query.join(Type).filter(Type_Preference.user_id == session["user_id"]).all()

    if trait_preferences == None or type_preferences == None:
        flash("Please set preferences prior to looking for matches.")
        return redirect(url_for('preferences'))

    # array storing currently saved preferences from table
    current_trait_prefs = []
    current_type_prefs = []

    for trait in trait_preferences:
        current_trait_prefs.append(trait.trait_id)

    for species in type_preferences:
        current_type_prefs.append(species.type_id)

    print("TYPE AND TRAIT PREFERENCES")
    print(current_type_prefs)
    print(current_trait_prefs)

    # pull all animals that match type preference in db
    animals = Animal.query.filter(Animal.type_id.in_(current_type_prefs)).all()

    # animal ids that meet criteria and set match criteria
    ids = []
    match = True

    for animal in animals:
        animal_profile = Animal_Profile.query.filter(Animal_Profile.animal_id == animal.id).all()
        print(animal.name)

        for trait in animal_profile:
            # if trait not in preferences then not a match 
            # unless trait is "kids" or "animals" as this is special case where animals w/ & w/o this are a match
            if trait.trait_id not in current_trait_prefs:
                 if trait.trait_id not in [8, 9]:
                    match = False

            print(trait.trait_id)
            print(match)

        #if animal is a match add id to list of matches
        if match:
            ids.append(animal.id)
        # reset match variable to True for next animal
        match = True

    print("IDS THAT MATCH CRITERIA")
    print(ids)    
    # pull users matches and already viewed animals
    swipes = Swipe.query.filter(Swipe.user_id == session["user_id"]).all()

    for swipe in swipes:
        if swipe.animal_id in ids:
            ids.remove(swipe.animal_id)

    print("IDS WITH PREVIOUS MATCHES REMOVED")
    print(ids)

    # query db for animals that match preferences
    display_animals = Animal.query.filter(Animal.id.in_(ids)).all()
    random.shuffle(display_animals)

    print("ANIMALS TO BE DISPLAYED ON MATCH PAGE")
    print(display_animals)

    return render_template('match.html', animals=display_animals)

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
