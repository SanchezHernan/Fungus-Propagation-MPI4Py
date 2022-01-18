from random import randrange
import time
from mpi4py import MPI

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

susceptibilidad = {
    'joven': 30,
    'adulto': 20,
    'viejo': 50,
}

porcent = {
    'joven': 1, 
    'adulto': 10, 
    'viejo': 45 
}

# Heridas abiertas: los árboles pueden presentar heridas en la corteza hechas por
# pájaros o insectos, las cuales sanan por sí solas pero aparecen al azar de una
# semana a otra con una probabilidad del 15% en plantas jóvenes, 5% en adultos y
# 30% en árboles viejos.

def calcularHeridas(edadArbol):
    heridas = False
    porcentaje = randrange(100)
    if edadArbol == 'adulto':
        if porcentaje < 5:
            heridas = True
    elif edadArbol == 'joven':
        if porcentaje < 15:
            heridas = True
    else:
        if porcentaje < 30:
            heridas = True
    return heridas

def crearMatriz(m, n):
    matriz = []
    estado = ''
    edad = ''
    for i in range(m):
        matriz.append([])
        for j in range(n):
            r = randrange(1000)
            if r < 500:
                estado = 'V'
            elif r >= 507:
                if randrange(2) == 0: estado = 'B'
                else: estado = 'A'
            elif  502 <= r < 507: estado = 'N'
            else: estado = 'R'

            r = randrange(100)
            if r < 54: edad = 'adulto'
            elif r < 84: edad = 'joven'
            else: edad = 'viejo'

            heridas = calcularHeridas(edad)
            casilla = {'estado': estado, 'edad': edad, 'heridas': heridas, 'semana': 0}
            matriz[i].append(casilla)
    return matriz

def calcularProbContagio(nVecinos, vecinosCS, arbol):
    porcVCS = vecinosCS * 100 // nVecinos
    suscept = susceptibilidad[arbol['edad']]
    if arbol['heridas']:
        suscept += 15
    return (porcVCS + suscept) * 0.6 + 5 #prob contagio

def getVecinosInfectados(matriz, i, j):
    infectados = 0
    vectorVecinos = []
    m = len(matriz)
    n = len(matriz[0])

    #creo el vectorVecinos segun la posicion de i y j
    if i == 0:
        if j == 0:
            vectorVecinos = [matriz[0][1], matriz[1][0], matriz[1][1]]        
        elif j >= n-1:
            vectorVecinos = [matriz[0][j-1], matriz[1][j-1], matriz[1][j]]
        else:
            vectorVecinos = [matriz[0][j-1], matriz[0][j+1], matriz[1][j-1], matriz[1][j], matriz[1][j+1]]
    elif i == m-1:
        if j == 0:
            vectorVecinos = [matriz[i-1][0], matriz[i-1][1], matriz[i][1]]        
        elif j >= n-1:
            vectorVecinos = [matriz[i-1][j-1], matriz[i-1][j], matriz[i][j-1]]
        else:
            vectorVecinos = [matriz[i-1][j-1], matriz[i-1][j], matriz[i-1][j+1], matriz[i][j-1], matriz[i][j+1]]
    elif j == 0:
        vectorVecinos = [matriz[i-1][j], matriz[i-1][j+1], matriz[i][j+1], matriz[i+1][j], matriz[i+1][j+1]]
    elif j == n-1:
        vectorVecinos = [matriz[i-1][j-1], matriz[i-1][j], matriz[i][j-1], matriz[i+1][j-1], matriz[i+1][j]]
    else:
        vectorVecinos = [
            matriz[i-1][j-1], matriz[i-1][j], matriz[i-1][j+1], matriz[i][j-1], matriz[i][j+1], matriz[i+1][j-1], matriz[i+1][j], matriz[i+1][j+1]
        ]

    #cuento los infectados entre los vecinos
    for vecino in vectorVecinos:
        if vecino['estado'] == 'R':
            infectados += 1
    
    return infectados

def arbolSano(arbol, vecinosCS):
    #el n de vecinos se toma siempre como 8 independientemente de si es un arbol de una esquina
    newArbol = arbol
    probContagio = calcularProbContagio(8, vecinosCS, newArbol)
    if randrange(100) < probContagio:
        newArbol['estado'] = 'N'
        newArbol['semana'] = 0
    return newArbol

def arbolConEsporas(arbol):
    newArbol = arbol
    if arbol['semana'] >= 5:
        newArbol['estado'] = 'R'
    newArbol['semana'] += 1
    return newArbol

def arbolConSintomas(arbol):
    newArbol = arbol
    newArbol['semana'] += 1
    if randrange(100) < 90:
        newArbol['estado'] = 'A'
    return newArbol
       
def arbolConTratamiento(arbol):
    newArbol = arbol
    r = randrange(100)
    porc = porcent[arbol['edad']]

    if arbol['semana'] < 8:
        if r < porc:
            newArbol['estado'] = 'V'
            newArbol['semana'] = 0
        else: newArbol['semana'] += 1
    else:
        if arbol['edad'] == 'joven' or arbol['edad'] == 'adulto':
            newArbol['estado'] = 'B'
        else:
            newArbol['estado'] = 'V'
            newArbol['edad'] = 'joven'
        newArbol['semana'] = 0
    return newArbol
    
def arbolPodado(arbol):
    newArbol = arbol
    newArbol['semana'] += 1
    if arbol['semana'] == 7:
        newArbol['estado'] = 'V'
    return newArbol

def cambiarEstado(matriz, li, ls):
    nuevaMatriz = []
    if li != 0: nuevaMatriz.append(matriz[0])
    for i in range(li, ls):
        nuevaMatriz.append([])
        for j in range(len(matriz[0])):
            arbol = matriz[i][j]
            estado = arbol['estado']
            if estado == 'V':
                vecinosCS = getVecinosInfectados(matriz, i, j)
                nuevaMatriz[i].append(arbolSano(arbol, vecinosCS))
            elif estado == 'N': nuevaMatriz[i].append(arbolConEsporas(arbol))
            elif estado == 'R': nuevaMatriz[i].append(arbolConSintomas(arbol))
            elif estado == 'A': nuevaMatriz[i].append(arbolConTratamiento(arbol))
            else: nuevaMatriz[i].append(arbolPodado(arbol))
    if ls != len(matriz): nuevaMatriz.append(matriz[len(matriz)-1])
    return nuevaMatriz




#paralelo

def distribuirFilas(matriz):
    m = 0
    if rank == 0:
        m = len(matriz)
    m = comm.bcast(m, root=0)
    dm = divmod(m, size)
    if rank == 0:
        print(rank, ': 0 a ', dm[0]+1)
        for i in range(1, size-1):
            comm.send(matriz[dm[0]*i-1], matriz[0]*(i+1), dest=i)
        comm.send(matriz[dm[0]*(size-1)-1], dm[0]*size + dm[1]-1)
    elif rank == size-1:
        print(rank, ': ', dm[0]*(size-1)-1, ' a ', dm[0]*size + dm[1])
    else:
        for i in range(1, size-1):
            if rank == i:
                print(rank, ': ',dm[0]*i-1, ' a ', dm[0]*(i+1)+1)
        if rank == 0: filas = dm[0] + dm[1] + 1
    

def compartirInformacion(matriz):
    if rank == 0:
        comm.send(matriz[len(matriz)-1], dest=1)
        matriz.append(comm.recv(source=1))
    elif rank != size-1:
        comm.send(matriz[0], dest=rank-1)
        comm.send(matriz[len(matriz)-1], dest=rank+1)
        matriz.insert(0, comm.recv(source=rank-1))
        matriz.append(comm.recv(source=rank+1))
    else:
        comm.send(matriz[0], dest=size-2)
        matriz.insert(0, comm.recv(source=size-2))

def recompartirInformacion(matriz):
    if rank == 0:
        comm.send(matriz[len(matriz)-2], dest=1)
        matriz[len(matriz)-1] = comm.recv(source=1)
    elif rank != size-1:
        comm.send(matriz[1], dest=rank-1)
        comm.send(matriz[len(matriz)-2], dest=rank+1)
        matriz[0] = comm.recv(source=rank-1)
        matriz[len(matriz)-1] = comm.recv(source=rank+1)
    else:
        comm.send(matriz[1], dest=size-2)
        matriz[0]= comm.recv(source=size-2)



def arbolesMPI(m, n, semanas):
    dm = divmod(m, size)
    if rank == 0: filas = dm[0] + dm[1]
    else: filas = dm[0]
    mat = crearMatriz(filas, n)
    compartirInformacion(mat)
    for i in range(semanas):
        if rank == 0: mat = cambiarEstado(mat, 0, len(mat)-1)
        elif rank != size-1: mat = cambiarEstado(mat, 1, len(mat)-1)
        else: mat = cambiarEstado(mat, 1, len(mat))
        recompartirInformacion(mat)
    if rank == 0: mat = mat[:len(mat)-1]
    elif rank != size-1: mat = mat[1:len(mat)-1]
    else: mat = mat[1:]


def printMatriz(matriz):
    txt = ''
    for fila in matriz:
        txt = '{'
        for j in range(len(fila)-1):
            txt += fila[j]['estado'] + ','
        txt += fila[len(fila)-1]['estado'] +'}'
        print(txt)


#ejecucion en paralelo
m= 800
r = 0
if rank == 0: r = randrange(96, 3000)
r = comm.bcast(r, root=0)
if rank == 0: print('semanas:', r, ', casillas: ', m)
inicio = time.time()
arbolesMPI(m, m, r)
fin = time.time()
print('tiempo:', fin - inicio)


#ejecucion secuencial
# m=200
# matriz = crearMatriz(m, m)
# r = randrange(96, 4000)
# print('semanas:', r, ', casillas: 200')
# inicio = time.time()
# for i in range(r):
#     matriz=cambiarEstado(matriz, 0, m)
# fin = time.time()
# print('tiempo:', fin - inicio)