import multiprocessing
from sympy.parsing.sympy_parser import parse_expr

def parse(expression, return_dict):
    return_dict[expression] = parse_expr(expression)

def calc(expression):
    manager = multiprocessing.Manager()
    return_dict = manager.dict()
    p = multiprocessing.Process(target=parse, args=(expression, return_dict))
    p.start()

    p.join(4)

    if p.is_alive():
        print('Terminated due to timeout')
        p.terminate()
        p.join()
    else:
        return return_dict[expression]
