import os
from flask import Flask, render_template, session, redirect, url_for, request, flash
from flask_bootstrap import Bootstrap
from flask_uploads import UploadSet, configure_uploads, IMAGES, patch_request_class
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField, PasswordField, IntegerField, FloatField, BooleanField, RadioField, SelectField
from wtforms.validators import DataRequired, Length, Email
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc
from datetime import datetime
import time
from werkzeug.security import generate_password_hash, check_password_hash

def create_app():
    basedir = os.path.abspath(os.path.dirname(__file__))
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'sdfh723809fog2o3h2cw'
    
    Bootstrap(app)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # lokacija slika 
    app.config['UPLOADS_DEFAULT_DEST'] = os.path.join(basedir, 'static/images')

    return app

app = create_app()

slike = UploadSet('pizzas', IMAGES)
configure_uploads(app, slike)
patch_request_class(app)

db = SQLAlchemy(app)

# default slika
placeholderSrc = '../static/images/pizzas/placeholder.png'

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Email(message="Username has to be in the form of email")])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, message="Password has to be 8 characters or longer!")])
    submit = SubmitField('Login')

class AdminAddPizza(FlaskForm):
    pizzaName = StringField('Naziv pizze:', validators=[DataRequired(message="Obvezan unos naziva pizze!")], render_kw={"placeholder": "e.g. PIZZA MARGARITA"})
    ingredients = StringField('Sastojci:', validators=[DataRequired(message="Obvezan unos glavnih sastojaka!")], render_kw={"placeholder": "e.g. sir, rajčica, ..."})
    priceRegular = FloatField('Cijena obične pizze:', validators=[DataRequired(message="Obvezan unos za cijenu obične pizze!")], render_kw={"placeholder": "e.g. 30"})
    priceJumbo = FloatField('Cijena jumbo pizze:', validators=[DataRequired(message="Obvezan unos za cijenu jumbo pizze!")], render_kw={"placeholder": "e.g. 50"})
    image = FileField('Slika:', validators=[FileAllowed(slike, 'Samo slika!')])
    submit = SubmitField('Dodaj')

class AdminEditPizza(FlaskForm):
    pizzaName = StringField('Naziv pizze:', validators=[DataRequired(message="Obvezan unos naziva pizze!")], render_kw={"placeholder": "e.g. PIZZA MARGARITA"})
    ingredients = StringField('Sastojci:', validators=[DataRequired(message="Obvezan unos glavnih sastojaka!")], render_kw={"placeholder": "e.g. sir, rajčica, ..."})
    priceRegular = FloatField('Cijena obične pizze:', validators=[DataRequired(message="Obvezan unos za cijenu obične pizze!")], render_kw={"placeholder": "e.g. 30"})
    priceJumbo = FloatField('Cijena jumbo pizze:', validators=[DataRequired(message="Obvezan unos za cijenu jumbo pizze!")], render_kw={"placeholder": "e.g. 50"})
    image = FileField('Slika:', validators=[FileAllowed(slike, 'Samo slika!')])
    save = SubmitField('Spremi')
    cancel = SubmitField('Odustani')

class AdminDeletePizza(FlaskForm):
    yes = SubmitField('Yes')
    no = SubmitField('No')

class Dodaj(FlaskForm):
    regOrJumbo = RadioField(label='Veličina: ', choices=[('regular', 'Regular'), ('jumbo', 'Jumbo')])
    kolicina = SelectField('Količina: ', choices=[('1', '1', ), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')])
    dodaj = SubmitField('Dodaj u košaricu')

class Dalje(FlaskForm):
    dalje = SubmitField('Dalje')

class Natrag(FlaskForm):
    natrag = SubmitField('Natrag na početnu')

class CheckOut(FlaskForm):
    ime = StringField('Ime:', validators=[DataRequired(message="Obvezan unos imena!")])
    prezime = StringField('Prezime:', validators=[DataRequired(message="Obvezan unos prezimena!")])
    telefon = IntegerField('Broj telefona:', validators=[DataRequired(message="Obvezan unos broja telefona!")])
    adresa = StringField('Adresa:', validators=[DataRequired(message="Obvezan unos adrese!")])
    naruci = SubmitField('Naruči')

class Order(db.Model):
    __tablename__ = 'order'
    id = db.Column(db.Integer, primary_key=True)
    ime = db.Column(db.String(64))
    prezime = db.Column(db.String(64))
    telefon = db.Column(db.String(64))
    adresa = db.Column(db.String(64))
    ukupno = db.Column(db.Float())
    vrijeme = db.Column(db.DateTime())
    narudzba = db.Column(db.Text())
    def __repr__(self):
        return '{},{},{},{},{},{}%{}'.format(self.ime, self.prezime, self.telefon, self.adresa, self.ukupno, self.vrijeme, self.narudzba)

class Pizzas(db.Model):
    __tablename__ = 'pizzas'
    id = db.Column(db.Integer, primary_key=True)
    pizzaName = db.Column(db.String(64), unique=True)
    ingredients = db.Column(db.String(128))
    priceRegular = db.Column(db.Float())
    priceJumbo = db.Column(db.Float())
    imageSrc = db.Column(db.String())
    def __repr__(self):
        return '{}, {}, {}, {}, {}'.format(self.pizzaName, self.ingredients, self.priceRegular, self.priceJumbo, self.imageSrc)

class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    password = db.Column(db.String(64))
    def __repr__(self):
        return '{}, {}'.format(self.username, self.password)



@app.route('/', methods=['GET', 'POST'])
def listPizzas():
    addForm = AdminAddPizza()

    ukupno = 0

    if session.get('pizza') is not None:
        for i in session['pizza']:
            ukupno += float(i[2]) * int(i[3])
        session['ukupno'] = ukupno
    else:
        session['pizza'] = []

    if session.get('bad') is None:
        session['bad'] = False

    if request.method == 'GET':
        data = Pizzas.query.all()
        return render_template('index.html', addForm=addForm, username=session.get('username'), data=data, broj_u_kosarici=session.get('broj_u_kosarici'), bad=session.get('bad'), pizza=session.get('pizza'), ukupno=session.get('ukupno'))

    elif request.method == 'POST' and addForm.validate_on_submit():
        # provjera da li je slika učitana ili nije
        if addForm.image.data == None:
            path = placeholderSrc
        else:
            filename = slike.save(addForm.image.data)
            path = slike.url(filename)

        session['bad'] = False
        temp = Pizzas(pizzaName=addForm.pizzaName.data, ingredients=addForm.ingredients.data, priceRegular=addForm.priceRegular.data, priceJumbo=addForm.priceJumbo.data, imageSrc=path)
        try:
            db.session.add(temp)
            db.session.commit()
            flash('Uspješno ste dodali: ' + temp.pizzaName)
            return redirect(url_for('listPizzas'))
        except exc.IntegrityError as e:
            db.session().rollback()
            session['bad'] = True
            flash('Već postoji pizza pod istim imenom!')
            return redirect(url_for('listPizzas'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def editDB(id):
    editForm = AdminEditPizza()
    pizza = Pizzas.query.get(id)
    old = pizza.pizzaName

    # zaštita od neodobrenog ulaska
    if request.method == 'GET' and session.get('username') is not None:
        # dohvaćanje podataka iz baze
        name = pizza.pizzaName
        ingre = pizza.ingredients
        priceReg = pizza.priceRegular
        priceJumbo = pizza.priceJumbo
        image = pizza.imageSrc

        # popunjavanje forme
        editForm.pizzaName.data = name
        editForm.ingredients.data = ingre
        editForm.priceRegular.data = priceReg
        editForm.priceJumbo.data = priceJumbo

        return render_template('edit-modal.html', editForm=editForm);
    
    elif request.method == 'GET' and session.get('username') is None:
        flash('Neodobren pristup!')
        return redirect(url_for('no_autho'))

    # kada se pritisne gumb save
    elif request.method == 'POST' and editForm.validate_on_submit() and editForm.save.data:
        # provjera da li je slika učitana ili nije
        if editForm.image.data == None:
            path = pizza.imageSrc
        else:
            # u slučaju da nije stavlja placeholder sliku
            filename = slike.save(editForm.image.data)
            path = slike.url(filename)

        pizza.pizzaName = editForm.pizzaName.data
        pizza.ingredients = editForm.ingredients.data
        pizza.priceRegular = editForm.priceRegular.data
        pizza.priceJumbo = editForm.priceJumbo.data
        pizza.imageSrc = path

        db.session.commit()
        session['bad'] = False
        flash('Uspješno ste uredili ' + old)
        
        return redirect(url_for('listPizzas'))

    elif editForm.cancel.data:
        return redirect(url_for('listPizzas'))

@app.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete(id):
    deleteForm = AdminDeletePizza()
    temp = Pizzas.query.get(id)

    # zaštita od neodobrenog ulaska
    if request.method == 'GET' and session.get('username') is not None:
        return render_template('delete-modal.html', deleteForm=deleteForm, pizzaName=temp.pizzaName)

    elif request.method == 'GET' and session.get('username') is None:
        flash('Neodobren pristup!')
        return redirect(url_for('no_autho'))

    elif request.method == 'POST' and deleteForm.validate_on_submit() and deleteForm.yes.data:
        db.session.delete(temp)
        db.session.commit()
        flash('Uspješno ste izbrisali: ' + temp.pizzaName)
        session['bad'] = False
        return redirect(url_for('listPizzas'))

    elif request.method == 'POST' and deleteForm.validate_on_submit() and deleteForm.no.data:
        return redirect(url_for('listPizzas'))

@app.route('/forbidden', methods=['GET', 'POST'])
def no_autho():
    natragForm = Natrag()
    if request.method == 'GET':
        return render_template('no-autho.html', natragForm=natragForm)
    elif request.method == 'POST':
        if natragForm.validate_on_submit():
            return redirect(url_for('listPizzas'))

# dodavanje u košaricu
@app.route('/dodaj/<int:id>', methods=['GET', 'POST'])
def dodaj(id):
    dodajForm = Dodaj()
    temp = Pizzas.query.get(id)

    if session.get('pizza') is None:
        lista = []
    else:
        lista = session.get('pizza')

    if session.get('broj_u_kosarici') is None:
        broj_u_kosarici = 0
    else:
        broj_u_kosarici = session.get('broj_u_kosarici')
    
    if request.method == 'GET':
        return render_template('dodaj.html', username=session.get('username'), dodajForm=dodajForm, broj_u_kosarici=session.get('broj_u_kosarici'), pizza=session.get('pizza'), ukupno=session.get('ukupno'))

    elif request.method == 'POST' and dodajForm.validate_on_submit() and dodajForm.regOrJumbo.data == 'regular':
        lista.append([temp.pizzaName, 'Regular', temp.priceRegular, dodajForm.kolicina.data])
        session['pizza'] = lista
        session['broj_u_kosarici'] = broj_u_kosarici + 1
        flash('Uspješno ste dodali ' + temp.pizzaName + ' u košaricu!')
        return redirect(url_for('listPizzas'))

    elif request.method == 'POST' and dodajForm.validate_on_submit() and dodajForm.regOrJumbo.data == 'jumbo':
        lista.append([temp.pizzaName, 'Jumbo', temp.priceJumbo, dodajForm.kolicina.data])
        session['pizza'] = lista
        session['broj_u_kosarici'] = broj_u_kosarici + 1
        flash('Uspješno ste dodali ' + temp.pizzaName + ' u košaricu!')
        return redirect(url_for('listPizzas'))

    else:
        flash('Niste odabrali veličinu!')
        return render_template('dodaj.html', username=session.get('username'), dodajForm=dodajForm, broj_u_kosarici=session.get('broj_u_kosarici'), ukupno=session.get('ukupno'))

@app.route('/kosarica', methods=['GET', 'POST'])
def cart():
    daljeForm = Dalje()
    natragForm = Natrag()

    if request.method == 'GET':
        return render_template('cart.html', pizza=session.get('pizza'), daljeForm=daljeForm, natragForm=natragForm, ukupno=session.get('ukupno'), username=session.get('username'), broj_u_kosarici=session.get('broj_u_kosarici'))

    elif request.method == 'POST':
        if daljeForm.validate_on_submit() and len(session['pizza']) != 0:
            return redirect(url_for('checkOut'))
    
        elif natragForm.validate_on_submit():
            return redirect(url_for('listPizzas'))


@app.route('/check-out', methods=['GET', 'POST'])
def checkOut():
    check = CheckOut()

    if request.method == 'GET':
        return render_template('check-out.html', pizza=session.get('pizza'), check=check, username=session.get('username'), broj_u_kosarici=session.get('broj_u_kosarici'))

    elif request.method == 'POST' and check.validate_on_submit():
        temp = Order(ime=check.ime.data, prezime=check.prezime.data, telefon=check.telefon.data, adresa=check.adresa.data, ukupno=session.get('ukupno'), vrijeme=datetime.now(), narudzba=str(session['pizza']))
        session['bad'] = False
        try:
            db.session.add(temp)
            db.session.commit()
            flash('Hvala Vam na ukazanom povjerenju!')
            session['pizza'] = []
            session['broj_u_kosarici'] = 0
            session['ukupno'] = None
            return redirect(url_for('listPizzas'))
        except exc.IntegrityError as e:
            db.session().rollback()
            session['bad'] = True
            flash('Već postoji pizza pod istim imenom!')
            return redirect(url_for('listPizzas'))

@app.route('/o-nama')
def o_nama():
    return render_template('o-nama.html', username=session.get('username'), broj_u_kosarici=session.get('broj_u_kosarici'), ukupno=session.get('ukupno'), pizza=session.get('pizza'));

@app.route('/kontakt')
def kontakt():
    return render_template('kontakt.html', username=session.get('username'), broj_u_kosarici=session.get('broj_u_kosarici'), ukupno=session.get('ukupno'), pizza=session.get('pizza'))

@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    users = Users.query.first()    
    
    if users == []:
        temp = Users(username="admin@admin.com", password=generate_password_hash('adminadmin'))
        db.session.add(temp)
        db.session.commit()
        users = Users.query.first()
        strVersion = str(users)
        lista = strVersion.split(', ')
        usrName = lista[0]
        pswd = lista[1]
    else:
        strVersion = str(users)
        lista = strVersion.split(', ')
        usrName = lista[0]
        pswd = lista[1]

    if request.method == 'POST':
        if form.validate_on_submit() and check_password_hash(pswd, form.password.data) and form.username.data == usrName:
            session['username'] = form.username.data
            flash('Dobrodošli!')
            return redirect(url_for('listPizzas'))

        elif form.validate_on_submit() and check_password_hash(pswd, form.password.data) is False or form.username.data != usrName:
            flash('Upisali ste neispravno korisničko ime ili zaporku!')
            return redirect(url_for('login'))

    return render_template('login.html', form=form, username=session.get('username'), broj_u_kosarici=session.get('broj_u_kosarici'), ukupno=session.get('ukupno'), pizza=session.get('pizza'))

@app.route('/#usluge')
def usluge():
    return render_template('index.html#usluge');

@app.route('/#meni')
def meni():
    return render_template('index.html#meni');

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('listPizzas'));

@app.route('/ukloni/<int:id>', methods=['GET'])
def ukloniIzKosarice(id):
    tempList = session.get('pizza')
    del tempList[id]
        
    session['broj_u_kosarici'] = session['broj_u_kosarici']-1
    session['pizza'] = tempList
    return redirect(url_for('cart'));

@app.route('/narudzbe', methods=['GET', 'POST'])
def izlistajNarudzbe():
    narudzbeQuery = Order.query.all()
    ids = [x.id for x in Order.query.all()]

    sviPodatci = []
    sveNarudzbe = []

    # raspetljavanje loše modelirane baze
    for i in narudzbeQuery:
        strVersion = str(i)
        lista = strVersion.split('%')
        podatci = lista[0]
        narudzbe = lista[1]

        podatci = podatci.split(',')
        sviPodatci.append(tuple(podatci))
        narudzbe = eval(narudzbe)
        sveNarudzbe.append(tuple(narudzbe))
    
    # zaštita od neodobrenog ulaska
    if request.method == 'GET' and session.get('username') is not None:
        return render_template('orders.html', username=session.get('username'), broj_u_kosarici=session.get('broj_u_kosarici'), ids=ids, podatci=sviPodatci, narudzbe=sveNarudzbe, ukupno=session.get('ukupno'), pizza=session.get('pizza'))

    elif request.method == 'GET' and session.get('username') is None:
        flash('Neodobren pristup!')
        return redirect(url_for('no_autho'))

@app.route('/izbrisi-narudzbu-iz-baze/<int:id>', methods=['GET', 'POST'])
def izbrisiNarudzbu(id):
    narudzba = Order.query.get(id)

    # zaštita od neodobrenog ulaska
    if request.method == 'GET' and session.get('username') is not None:
        try:
            db.session.delete(narudzba)
            db.session.commit()
            flash('Uspješno ste izbrisali narudžbu pod rednim brojem: ' + str(narudzba.id))
            session['bad'] = False
        except exc.IntegrityError as e:
            db.session().rollback()
            session['bad'] = True
            flash('Ne postoji narudžba pod tim brojem!')
        return redirect(url_for('listPizzas'))
    
    elif request.method == 'GET' and session.get('username') is None:
        flash('Neodobren pristup!')
        return redirect(url_for('no_autho'))

@app.errorhandler(404)
def page_not_found(e):
	return render_template('404.html', username=session.get('username'), broj_u_kosarici=session.get('broj_u_kosarici'), bad=session.get('bad'), pizza=session.get('pizza'), ukupno=session.get('ukupno')), 404;
	
@app.errorhandler(500)
def internal_server_error(e):
	return render_template('500.html', username=session.get('username'), broj_u_kosarici=session.get('broj_u_kosarici'), bad=session.get('bad'), pizza=session.get('pizza'), ukupno=session.get('ukupno')), 500;