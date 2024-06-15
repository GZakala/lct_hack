import logging

from functools import wraps
from typing import Callable


def get_logger(file_name: str) -> logging.Logger:
    logger = logging.getLogger(file_name)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(name)s\t%(asctime)s\t%(levelname)s\t%(message)s')

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger

def log_method(logger: logging.Logger, log_result: bool = True, log_args_kwargs: bool = True):
    def log_method_decorator(func: Callable):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if log_args_kwargs:
                logger.info(f'Calling method `{func.__name__}` of class `{self.__class__.__name__}` with args and kwargs: {args}, {kwargs}')
            else:
                logger.info(f'Calling method `{func.__name__}` of class `{self.__class__.__name__}`')

            result = func(self, *args, **kwargs)

            if log_result and log_args_kwargs:
                logger.info(f'Method `{func.__name__}` of class `{self.__class__.__name__}` with args and kwargs: {args}, {kwargs} returned {result}')
            elif log_result:
                logger.info(f'Method `{func.__name__}` of class `{self.__class__.__name__}` returned {result}')
            elif log_args_kwargs:
                logger.info(f'Method `{func.__name__}` of class `{self.__class__.__name__}` with args and kwargs: {args}, {kwargs} completed')
            else:
                logger.info(f'Method `{func.__name__}` of class `{self.__class__.__name__}` completed')

            return result
        return wrapper
    return log_method_decorator
            
def log_func(logger: logging.Logger, log_result: bool = True, log_args_kwargs: bool = True):
    def log_func_decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if log_args_kwargs:
                logger.info(f'Calling func `{func.__name__}` with args and kwargs: {args}, {kwargs}')
            else:
                logger.info(f'Calling func `{func.__name__}`')

            result = func(*args, **kwargs)

            if log_result and log_args_kwargs:
                logger.info(f'Func `{func.__name__}` with args and kwargs: {args}, {kwargs} returned {result}')
            elif log_result:
                logger.info(f'Func `{func.__name__}` returned {result}')
            elif log_args_kwargs:
                logger.info(f'Func `{func.__name__}` with args and kwargs: {args}, {kwargs} completed')
            else:
                logger.info(f'Func `{func.__name__}` completed')

            return result
        return wrapper
    return log_func_decorator

def log_init(logger: logging.Logger, log_args_kwargs: bool = True):
    def log_init_decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if log_args_kwargs:
                logger.info(f'Init class `{self.__class__.__name__}` with args and kwargs: {args}, {kwargs}')
            else:
                logger.info(f'Init class `{self.__class__.__name__}`')
                
            result = func(self, *args, **kwargs)

            if log_args_kwargs:
                logger.info(f'Class `{self.__class__.__name__}` with args and kwargs: {args}, {kwargs} inited')
            else:
                logger.info(f'Class `{self.__class__.__name__}` inited')
                
            return result
        return wrapper
    return log_init_decorator
