# -*- coding: utf-8 -*-

from flask import Flask, render_template, redirect, request, session, abort, flash, jsonify
import gspread, pprint, json, pandas, gc
from oauth2client.service_account import ServiceAccountCredentials
from flask import Response
from flask_bootstrap import Bootstrap
from flask_wtf import CsrfProtect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_required
from passlib.hash import sha256_crypt
from MySQLdb import escape_string as thwart
from forms import LoginForm, RegisterForm
from werkzeug.security import generate_password_hash, check_password_hash
from clases import ValoresGrafica
from clases import Valor
import re, json

app = Flask(__name__)
Bootstrap(app)
app.secret_key = 'TwitterAnalizer2016Apps'
csrf = CsrfProtect(app)
db = SQLAlchemy(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:1234@localhost/TwitterAnalizer'

#Modelos

class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombres = db.Column(db.String(50))
    apellidos = db.Column(db.String(50))
    username = db.Column(db.String(10), unique=True)
    email = db.Column(db.String(50))
    password = db.Column(db.String(150))

    def get_id():
        return id

    def is_authenticated(self):
        return True

    def is_active(self): # line 37
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    # Required for administrative interface
    def __unicode__(self):
        return self.username

#Views

@app.route('/')
def index():
    return render_template("base.html")

@app.route('/documentos')
def documentos():
    return render_template("documentos.html")


@app.route('/register')
def register():
    form = RegisterForm()
    return render_template('register.html', form=form)

@app.route('/guardarUsuario', methods=['POST'])
def guardarUsuario():
    form = RegisterForm()
    if request.method == "POST":
        nombres = str(form['nombres'].data)
        apellidos = str(form['apellidos'].data)
        email = str(form['email'].data)
        username = str(form['username'].data)
        password1 = str(form['password1'].data)
        password2 = str(form['password2'].data)
        if password1 == password2:
            if form.validate():
                usuarioExistente = Usuario.query.filter_by(username=username).first()
                if usuarioExistente:
                    flash('El nombre de usuario ingresado ya se encuentra registrado. Por favor, ingrese uno nuevo.')
                else:
                    password = generate_password_hash(password1, method='sha256')
                    usuario = Usuario(nombres=nombres, apellidos=apellidos, username=username, email=email, password=password)
                    db.session.add(usuario)
                    db.session.commit()
                    flash('Registro exitoso!')
            else:
                flash('Informacion Incorrecta.')
                if len(nombres)<4 or len(nombres)>50:
                    flash("Los nombres deben tener entre 4 y 50 caracteres.")

                if len(apellidos)<4 or len(apellidos)>50:
                    flash("Los apellidos deben tener entre 4 y 50 caracteres.")

                if len(email)<4 or len(email)>50:
                    flash("El email debe tener entre 4 y 50 caracteres.")

                if len(username)<4 or len(username)>10:
                    flash("El username debe tener entre 4 y 10 caracteres.")

                if len(password1)<4 or len(password1)>10:
                    flash("El password debe tener entre 4 y 10 caracteres.")
        else:
            flash("Los password ingresados no son iguales. Ingreselos nuevamente.")

    return redirect('/register')

@app.route('/login')
def login():
    form = LoginForm()
    return render_template('login.html', form=form)

@app.route('/autenticacion', methods=['POST'])
def autenticacion():
    form = LoginForm()
    if request.method == "POST":
        if form.validate():
            username = str(form['username'].data)
            password = str(form['password'].data)
            usuario = Usuario.query.filter_by(username=username).first()
            if usuario:
                if check_password_hash(usuario.password, password):
                    return redirect('/dashboard')
            else:
                flash("Las credenciales son erroneas. Ingreselas nuevamente.")
                return redirect('/login')
        else:
            flash("La informacion ingresada es erronea. Ingrese nuevamente.")
            return redirect('/login')

def jsonDefault(object):
    return object.__dict__

@app.route('/dashboard')
def dashboard():
    return render_template('contenido.html')

@app.route('/obtenerDatosGenerales', methods=['POST', 'GET'])
def obtenerDatosGenerales():
    listaValoresJson = []
    dataFrameOriginal = cargarDataFrame()
    listaValoresJson = (consultaTweetsRetweets(dataFrameOriginal))
    listaValoresJson = json.dumps(listaValoresJson, default=jsonDefault)
    return app.response_class(
        response=listaValoresJson,
        status=200,
        mimetype='text/json'
    )

@app.route('/obtenerDatos', methods=['POST', 'GET'])
def obtenerDatos():
    listaValoresJson = []
    dataFrameOriginal = cargarDataFrame()
    listaValoresJson.append(consultaTweetsRetweets(dataFrameOriginal))
    listaValoresJson.append(consultaFrecuenciaHoras(dataFrameOriginal['Fecha']))
    listaValoresJson.append(consultaFrecuenciaDinero(dataFrameOriginal['Contenido']))
    listaValoresJson.append(consultaHashtagsMasUsados(dataFrameOriginal['Contenido']))
    #listaValoresJson.append(consultaHorasCitadas(dataFrameOriginal['Contenido']))
    listaValoresJson.append(consultaParticipacionCuentas(dataFrameOriginal['Usuarios']))
    listaValoresJson = json.dumps(listaValoresJson, default=jsonDefault)
    return app.response_class(
        response=listaValoresJson,
        status=200,
        mimetype='text/json'
    )

@app.route('/obtenerNube', methods=['POST', 'GET'])
def obtenerNube():
    dataFrameOriginal = cargarDataFrame()
    valoresGrafica = consultaParticipacionCuentas(dataFrameOriginal['Usuarios'])
    cadena = ''
    for valor in valoresGrafica.lstValores:
        cadena = cadena +" "+ unicode(valor.name)
    valorJson = json.dumps(cadena, default=jsonDefault)
    return app.response_class(
        response=valorJson,
        status=200,
        mimetype='text/json'
    )

def cargarDataFrame():
    dataFrameGeneral = pandas.DataFrame({'Fecha':abrirCuenta().col_values(4), 'Contenido':abrirCuenta().col_values(3),
    'Usuarios':abrirCuenta().col_values(2), 'Entidades':abrirCuenta().col_values(18)})
    return dataFrameGeneral

def consultaParticipacionCuentas(serieUsuarios):
    dfUsuarios = pandas.DataFrame({'Usuarios':serieUsuarios.tolist()})
    listaEtiquetas = sorted(dfUsuarios.groupby('Usuarios').groups.keys())
    listaResultados = dfUsuarios.groupby('Usuarios').size().values.tolist()
    dfUsuariosSorted = pandas.DataFrame({'Etiquetas':listaEtiquetas, 'Resultados':listaResultados})
    dfUsuariosSorted = dfUsuariosSorted.sort_values(by=('Resultados'),ascending=[False]).head(30)
    listaEtiquetas = dfUsuariosSorted['Etiquetas'].tolist()
    listaResultados = dfUsuariosSorted['Resultados'].tolist()
    listaValores = []
    for i in range (len(listaEtiquetas)):
        listaValores.append(Valor(name=listaEtiquetas[i], y=listaResultados[i]))
    return ValoresGrafica(nombreGrafica="30 cuentas con mayor participación", nombreSerie="Participaciones", lstValores=listaValores,
    tipoGrafico="column", descripcion="Muestra las 20 horas más referenciadas en las descripciones de los tweets")

def consultaTotalCuentas(serieUsuarios):
    dfUsuarios = pandas.DataFrame({'Usuarios':serieUsuarios.tolist()})
    listaEtiquetas = dfUsuarios.drop_duplicates(subset='Usuarios', keep='first', inplace=False).values.tolist()
    return Valor(name="Usuarios participantes", y=len(listaEtiquetas)-2)

def consultaTweetsRetweets(dataFrameOriginal):
    listaEtiquetas = ['Tweets', 'Retweets']
    dfResultado = pandas.DataFrame({'Resultado':dataFrameOriginal['Contenido'].str.contains("RT").values.tolist()})
    listaResultados = dfResultado.groupby(['Resultado']).size().values.tolist()
    listaValores = []
    for i in range (len(listaEtiquetas)):
        listaValores.append(Valor(name=listaEtiquetas[i], y=listaResultados[i]))
    return ValoresGrafica(nombreGrafica="TWEETS Y RETWEETS", nombreSerie="Interacciones", lstValores=listaValores,
    tipoGrafico="pie", descripcion="Muestra la cantidad de tweets y retweets existentes.")

def consultaHorasCitadas(serieContenido):
    contenidoRecuperado = []
    listaContenido = serieContenido.tolist()
    for contenido in listaContenido:
        listaHoras = re.findall(r'\d\d:', contenido)
        for hora in listaHoras:
            contenidoRecuperado.append(hora)
            print hora.remove

    dfHoras = pandas.DataFrame({'Horas':contenidoRecuperado})
    listaEtiquetas = sorted(dfHoras.groupby('Horas').groups.keys())
    listaResultados = dfHoras.groupby('Horas').size().values.tolist()
    dfHorasSorted = pandas.DataFrame({'Etiquetas':listaEtiquetas, 'Resultados':listaResultados})
    dfHorasSorted = dfHorasSorted.sort_values(by=('Resultados'),ascending=[False]).head(20)
    listaEtiquetas = dfHorasSorted['Etiquetas'].tolist()
    listaResultados = dfHorasSorted['Resultados'].tolist()
    listaValores = []
    for i in range (len(listaEtiquetas)):
        listaValores.append(Valor(name=listaEtiquetas[i], y=listaResultados[i]))
    return ValoresGrafica(nombreGrafica="Horas más referenciadas",
    nombreSerie="Número referencias", lstValores=listaValores, tipoGrafico="column",
    descripcion="Muestra las 20 horas más referenciadas en las descripciones de los tweets.")

def consultaFrecuenciaDinero(serieContenido):
    contenidoRecuperado = []
    listaContenido = serieContenido.tolist()
    for contenido in listaContenido:
        listaCantidadDinero = re.findall(r'\$+\d[0-9]*', contenido)
        for cantidad in listaCantidadDinero:
            contenidoRecuperado.append(cantidad)

    dfDinero = pandas.DataFrame({'Dinero':contenidoRecuperado})
    listaEtiquetas = sorted(dfDinero.groupby('Dinero').groups.keys())
    listaResultados = dfDinero.groupby('Dinero').size().values.tolist()
    dfDineroSorted = pandas.DataFrame({'Etiquetas':listaEtiquetas, 'Resultados':listaResultados})
    dfDineroSorted = dfDineroSorted.sort_values(by=('Resultados'),ascending=[False]).head(20)
    listaEtiquetas = dfDineroSorted['Etiquetas'].tolist()
    listaResultados = dfDineroSorted['Resultados'].tolist()
    listaValores = []
    for i in range (len(listaEtiquetas)):
        listaValores.append(Valor(name=listaEtiquetas[i], y=listaResultados[i]))
    return ValoresGrafica(nombreGrafica="VALORES DE COBROS O PAGOS",
    nombreSerie="Cobros", lstValores=listaValores, tipoGrafico="column",
    descripcion="Muestra los valores monetarios, con el signo $, más referenciados en los tweets.")

def consultaFrecuenciaHoras(serieFecha):
    serieFechaHora = serieFecha.str.split(' ').str[3]
    serieHoras = pandas.Series(serieFechaHora).str.split(':').str[0]
    dfHoras = pandas.DataFrame({'Horas':serieHoras.tolist()})
    listaEtiquetas = sorted(dfHoras.groupby('Horas').groups.keys())
    listaResultados = dfHoras.groupby('Horas').size().values.tolist()
    listaValores = []
    for i in range (len(listaEtiquetas)):
        listaValores.append(Valor(name=listaEtiquetas[i], y=listaResultados[i]))
    return ValoresGrafica(nombreGrafica="FRECUENCIA DE INTERACCIÓN POR HORA", nombreSerie="Frecuencia",
    lstValores=listaValores, tipoGrafico="column", descripcion="Muestra el grado de interacción que existe con el hashtag evaluado, por horas.")

def consultaHashtagsMasUsados(serieContenido):
    contenidoRecuperado = []
    listaContenido = serieContenido.tolist()
    for contenido in listaContenido:
        listaHashtags = re.findall(r'#\S+', contenido)
        for hashtag in listaHashtags:
            contenidoRecuperado.append(hashtag.upper())

    dfHashtags = pandas.DataFrame({'Hashtags':contenidoRecuperado})
    listaEtiquetas = sorted(dfHashtags.groupby('Hashtags').groups.keys())
    listaResultados = dfHashtags.groupby('Hashtags').size().values.tolist()
    dfHashtagsSorted = pandas.DataFrame({'Etiquetas':listaEtiquetas, 'Resultados':listaResultados})
    dfHashtagsSorted = dfHashtagsSorted.sort_values(by=('Resultados'),ascending=[False]).head(20)
    listaEtiquetas = dfHashtagsSorted['Etiquetas'].tolist()
    listaResultados = dfHashtagsSorted['Resultados'].tolist()
    listaValores = []
    for i in range (len(listaEtiquetas)):
        listaValores.append(Valor(name=listaEtiquetas[i], y=listaResultados[i]))
    return ValoresGrafica(nombreGrafica="Hashtags más utilizados", nombreSerie="Referencias", lstValores=listaValores,
    tipoGrafico="column", descripcion="Muestra los 20 hashtags más referenciados en los tweets.")

def consultaNumeroHashtagsMasUsados(serieEntidades):
    contenidoRecuperado = []
    listaSerieEntidades = serieEntidades.tolist()
    stringEncoded = json.dumps(listaSerieEntidades[1])
    print(stringEncoded)
    stringJson = json.loads(stringEncoded)
    print(type(stringJson))

    for elemento in stringJson:
        for entidad in elemento[0]:
            contenidoRecuperado.append(len(elemento['hashtags']))

    dfNumeroHashtags = pandas.DataFrame({'numeroHashtags':contenidoRecuperado})
    listaEtiquetas = sorted(dfNumeroHashtags.groupby('numeroHashtags').groups.keys())
    listaResultados = dfNumeroHashtags.groupby('numeroHashtags').size().values.tolist()
    dfNumeroHashtagsSorted = pandas.DataFrame({'Etiquetas':listaEtiquetas, 'Resultados':listaResultados})
    dfNumeroHashtagsSorted = dfNumeroHashtagsSorted.sort_values(by=('Resultados'),ascending=[False]).head(20)
    listaEtiquetas = dfNumeroHashtagsSorted['Etiquetas'].tolist()
    listaResultados = dfNumeroHashtagsSorted['Resultados'].tolist()
    listaValores = []
    for i in range (len(listaEtiquetas)):
        listaValores.append(Valor(name=listaEtiquetas[i], y=listaResultados[i]))
    return ValoresGrafica(nombreGrafica="Número de hashtags más citados", nombreSerie="Referencias", lstValores=listaValores, tipoGrafico="column")

def abrirCuenta():
    scope = ['http://spreadsheets.google.com/feeds']
    creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open('#sexo copy').sheet1
    return sheet
