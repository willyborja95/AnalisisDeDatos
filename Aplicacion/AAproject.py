#!/usr/bin/python
#-*- coding: utf-8 -*-

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pprint

import numpy as np
from matplotlib import pyplot as plt
from matplotlib import style


scope = ['http://spreadsheets.google.com/feeds']

creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)

client = gspread.authorize(creds)

#sheet = client.open('TAGS v6.1.6 #porn').sheet1
sheet = client.open('#sexo copy').sheet1

pp = pprint.PrettyPrinter()

#tags = sheet.get_all_records()
tags = sheet.col_values(16)
listaPaises = []
frecuencia = []
numeracion = []

for paisBuscado in tags:
    procesado = False
    for i in range (len(listaPaises)):
        if listaPaises[i] == paisBuscado:
            frecuencia[i]+=1
            procesado = True

    if procesado == False:
        listaPaises.append(paisBuscado)
        frecuencia.append(1)

for i in range(len(listaPaises)):
    numeracion.append(i)
    print(listaPaises[i]+"   "+str(frecuencia[i])+"\n")

plt.plot(numeracion, frecuencia)
plt.show()


#pp.pprint(len(tags))
