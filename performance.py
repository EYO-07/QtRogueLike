# performance.py
import time 

def tic():
    return time.perf_counter()

def toc(initial, message = "", ):
    print(f"{message} dt = {time.perf_counter() - initial:.3f}")

