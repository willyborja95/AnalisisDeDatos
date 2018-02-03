import pandas as pd

lista = [3,4,2,5,2,3,3,5,6,2,3,4,2,1,4,5,2]
df = pd.DataFrame({'a':lista})

listaEtiquetas = df.groupby('a').groups.keys()



print(df.groupby('a').size())
print("-----Etiquetas---------")
print(listaEtiquetas)
