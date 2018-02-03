class ValoresGrafica:
    lstValores = []

    def __init__(self, nombreGrafica, nombreSerie, lstValores, tipoGrafico, descripcion):
        self.lstValores = []
        self.setNombreSerie(nombreSerie)
        self.setNombreGrafica(nombreGrafica)
        self.setLstValores(lstValores)
        self.setTipoGrafico(tipoGrafico)
        self.setDescripcion(descripcion)

    def setNombreGrafica(self, nombreGrafica):
        self.nombreGrafica = nombreGrafica

    def getNombreGrafica(self):
        return self.nombreGrafica

    def setNombreSerie(self, nombreSerie):
        self.nombreSerie = nombreSerie

    def getNombreSerie(self):
        return self.nombreSerie

    def setLstValores(self, lstValores):
        self.lstValores = lstValores

    def getLstValores(self):
        return self.lstValores

    def setTipoGrafico(self, tipoGrafico):
        self.tipoGrafico = tipoGrafico

    def getTipoGrafico(self):
        return self.tipoGrafico

    def setDescripcion(self, descripcion):
        self.descripcion = descripcion

    def getDescripcion(self):
        return self.descripcion

    def __str__(self):
        return self.nombreGrafica

class Valor:
    name = ""
    y = ""

    def __init__(self, name, y):
        self.name = name
        self.y = y
