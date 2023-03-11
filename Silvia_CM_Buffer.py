import multiprocessing as mlp
import random
from time import sleep

NPROD = 10 #Número de productores
MAX = 1000000 #Cota superior de los números
NELEM = 10 #Cantidad de números que produce cada productor

def delay(factor = 3):
    sleep(random.random()/factor)

def terminado(estados_procesos): #Función para calcular cuando todos los productores han acabado de producir
    result = True
    for i in range(len(estados_procesos)):
        if estados_procesos[i] != -1:
            result = False
    return result

def producir(colas, estados_procesos, i, mutex):
    mutex.acquire() #no queremos que se modifique el array desde varios procesos, podria dar problemas
    try:
        act = last[i] #marcamos cual fue el ultimo numero que genero, para hacer la sucesion creciente
        x = random.randint(act,MAX)
        print(f"El productor {i} produce {x}")
        if estados_procesos[i] == -2: #si no hay nada guardado, se guarda ahi directamente
            estados_procesos[i]= x
        else:
            colas[i].put(x) #sino, se añade a la cola
        last[i] = x
        delay()
    finally:
        mutex.release() #liberamos

def productor(estados_procesos, i, Empty, NonEmpty, mutex, colas):
    for j in range(NELEM):
        Empty.acquire() #marcamos que vamos a colocar un elemento nuevo
        producir(colas, estados_procesos, i, mutex)
        NonEmpty.release() #marcamos que vamos a colocar un elemento nuevo
        delay()
    mutex.acquire() #no queremos que se modifique el array desde varios procesos, podria dar problemas
    colas[i].put(-1) #para marcar que hemos terminado de producir números
    mutex.release()
    NonEmpty.release()
    NonEmpty.release()
    print(f"El productor {i} ha terminado")

def consumir(colas, storage, estados_procesos, index, i):
    mutex.acquire() #igual que en producir, no queremos que se modifique desde dos procesos distintos
    try:
        storage[index.value] = estados_procesos[i]
        if(not colas[i].empty()):
            estados_procesos[i] = colas[i].get() #colocamos el siguiente de la cola
        index.value += 1
        delay()
    finally:
        mutex.release() #liberamos

def consumidor(colas, storage, estados_procesos, Empty, NonEmpty, index):
    for k in NonEmpty: # Para que no consuma si no han acabado todos de producir
        k.acquire() 
        k.acquire()
    while(not terminado(estados_procesos)):
        j = 0
        min = MAX + 1 #inicializamos
        for i in range(NPROD):
            if(estados_procesos[i] > 0 and estados_procesos[i] < min):
                min = estados_procesos[i] #buscamos el mínimo
                j = i
        if min != MAX + 1: #si se ha actualizado el minimo 
            print(f"Los estados actualmente son: ")
            print(estados_procesos[:])
            print(f"Consume {estados_procesos[j]}")
            consumir(colas, storage, estados_procesos, index, j)
            Empty[j].release() #marcamos que el elemento ha sido consumido
            NonEmpty[j].acquire() #marcamos que el elemento ha sido consumido
            delay()

if __name__ == "__main__":
    colas = [] #aqui vamos guardando los numeros que producen los procesos, en colas para ir rellenando a la que consumimos
    last = mlp.Array('i', NPROD) #guardamos cual fue el último número que se produjo, para que sea creciente
    estados_procesos = mlp.Array('i',NPROD)
    Empty = [mlp.BoundedSemaphore(NELEM) for i in range(NPROD)]
    NonEmpty = [mlp.Semaphore(0) for i in range(NPROD)]
    for k in range(NPROD):
        estados_procesos[k] = -2 #iniciamos todo vacío
        colas.append(mlp.Queue()) #añadimos las colas
        last[k] = 0 #el primer número tiene que ser >= 0
    mutex = mlp.Lock() #para las secciones críticas
    index = mlp.Value('i', 0) #para ir rellenando el storage
    storage = mlp.Array('i', 500) #aqui irá el resultado del merge
    procesos = [mlp.Process(target = productor, name = f"prod {i}",
                    args=(estados_procesos, i, Empty[i], NonEmpty[i], mutex, colas)) for i in range(NPROD)]
    consum = [mlp.Process(target = consumidor, name = "consumidor", 
                    args = (colas, storage, estados_procesos, Empty, NonEmpty, index))]
    for proc in procesos + consum:
        proc.start()
    for proc in procesos + consum:
        proc.join()
    print("El resultado es: ")
    for k in range(len(storage)):
        if storage[k] != 0:
            print(storage[k])



