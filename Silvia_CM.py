import multiprocessing as mlp
import random
from time import sleep

NPROD = 10 #Número de productores
MAX = 10000 #Cota superior de los números
NELEM = 7 #Cantidad de números que produce cada productor

def delay(factor = 3):
    sleep(random.random()/factor)

def producir(estados_procesos, i, mutex):
    mutex.acquire() #no queremos que se modifique el array desde varios procesos, podria dar problemas
    try:
        act = max(estados_procesos[i],0) #para asegurarnos de que genera los números de forma creciente
        x = random.randint(act,MAX) 
        print(f"El productor {i} produce {x}")
        estados_procesos[i] = x #actualizamos el estado
    finally:
        mutex.release()

def productor(estados_procesos, i, Empty, NonEmpty, mutex):
    for j in range(NELEM):
        Empty.acquire() #marcamos que vamos a colocar un elemento nuevo
        producir(estados_procesos, i, mutex)
        NonEmpty.release() #marcamos que vamos a colocar un elemento nuevo
        delay()
    mutex.acquire() #no queremos que se modifique el array desde varios procesos, podria dar problemas
    estados_procesos[i] = -1 #para marcar que hemos terminado de producir números
    mutex.release()
    NonEmpty.release()
    print(f"El productor {i} ha terminado")

def consumir(storage, estados_procesos, index, i):
    storage[index.value] = estados_procesos[i] #añadimos el número al storage
    index.value += 1 #avanzamos el índice
    delay()

def consumidor(storage, estados_procesos, Empty, NonEmpty, index):
    min = 0
    for i in NonEmpty:
        i.acquire()
    while(min != MAX +1):
        j = 0
        min = MAX + 1
        for i in range(NPROD):
            if(estados_procesos[i] > 0 and estados_procesos[i] < min):
                min = estados_procesos[i] #buscamos el mínimo
                j = i
        if min != MAX + 1: 
            print(f"Los estados actualmente son: ")
            print(estados_procesos[:])
            print(f"Consume {estados_procesos[j]}")
            consumir(storage, estados_procesos, index, j)
            Empty[j].release() #marcamos que pasa a estar vacio
            NonEmpty[j].acquire() #marcamos que pasa a estar vacio
            delay()

if __name__ == "__main__":
    estados_procesos = mlp.Array('i', NPROD)
    for k in range (NPROD):
        estados_procesos[k] = -2 # comenzamos con todo vacio
    #Empty y NonEmpty son para no consumir elementos que ya han sido consumidos y para que un productor
    #No produzca si aun no ha sido consumido
    Empty = [mlp.Lock() for i in range(NPROD)]
    NonEmpty = [mlp.Lock() for i in range(NPROD)]
    for proc in range(NPROD):
        NonEmpty[proc].acquire()
    mutex = mlp.Lock() #para las secciones críticas
    index = mlp.Value('i', 0) #para ir rellenando el storage
    storage = mlp.Array('i', 500) #aqui irá el resultado del merge
    procesos = [mlp.Process(target = productor, name = f"prod {i}",
                    args=(estados_procesos, i, Empty[i], NonEmpty[i], mutex)) for i in range(NPROD)]
    consum = [mlp.Process(target = consumidor, name = "consumidor", 
                    args = (storage, estados_procesos, Empty, NonEmpty, index))]
    for proc in procesos + consum:
        proc.start()
    for proc in procesos + consum:
        proc.join()
    print("El resultado es: ")
    for k in range(len(storage)):
        if storage[k] != 0:
            print(storage[k])



