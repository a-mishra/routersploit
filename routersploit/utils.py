from __future__ import print_function
import threading
from functools import wraps
import sys
import random
import string

import requests


print_lock = threading.Lock()

colors = {
    'grey': 30,  'red': 31,
    'green': 32, 'yellow': 33,
    'blue': 34,  'magenta': 35,
    'cyan': 36,  'white': 37,
}


def pythonize_path(path):
    """ Replace argument to valid python dotted notation.

    ex. foo/bar/baz -> foo.bar.baz
    """
    return path.replace('/', '.')


def humanize_path(path):
    """ Replace python dotted path to directory-like one.

    ex. foo.bar.baz -> foo/bar/baz

    :param path: path to humanize
    :return: humanized path

    """
    return path.replace('.', '/')


def module_required(fn):
    """ Checks if module is loaded.

    Decorator that checks if any module is activated
    before executing command specific to modules (ex. 'run').
    """
    @wraps(fn)
    def wrapper(self, *args, **kwargs):
        if not self.current_module:
            print_error("You have to activate any module with 'use' command.")
            return
        return fn(self, *args, **kwargs)
    try:
        name = 'module_required'
        wrapper.__decorators__.append(name)
    except AttributeError:
        wrapper.__decorators__ = [name]
    return wrapper


def stop_after(space_number):
    """ Decorator that determine when to stop tab-completion

    Decorator that tells command specific complete function
    (ex. "complete_use") when to stop tab-completion.
    Decorator counts number of spaces (' ') in line in order
    to determine when to stop.

        ex. "use exploits/dlink/specific_module " -> stop complete after 2 spaces
        "set rhost " -> stop completing after 2 spaces
        "run " -> stop after 1 space

    :param space_number: number of spaces (' ') after which tab-completion should stop
    :return:
    """
    def _outer_wrapper(wrapped_function):
        @wraps(wrapped_function)
        def _wrapper(self, *args, **kwargs):
            try:
                if len(args[1].split(' ', space_number)) == space_number + 1:
                    return []
            except Exception as err:
                print(err)
            return wrapped_function(self, *args, **kwargs)
        return _wrapper
    return _outer_wrapper


def __cprint(*args, **kwargs):
    """ Color print()

    Signature like Python 3 print() function
    print([object, ...][, sep=' '][, end='\n'][, file=sys.stdout])
    """
    if not kwargs.get("verbose", True):
        return

    with print_lock:
        color = kwargs.get('color', None)
        if color:
            file_ = kwargs.get('file', sys.stdout)
            sep = kwargs.get('sep', ' ')
            end = kwargs.get('end', '\n')
            print('\033[{}m'.format(colors[color]), end='', file=file_, sep=sep)
            print(*args, end='', file=file_, sep=sep)
            print('\033[0m', sep=sep, end=end, file=file_)
        else:
            print(*args, **kwargs)


def print_error(*args, **kwargs):
    __cprint('\033[91m[-]\033[0m', *args, **kwargs)


def print_status(*args, **kwargs):
    __cprint('\033[94m[*]\033[0m', *args, **kwargs)


def print_success(*args, **kwargs):
    __cprint('\033[92m[+]\033[0m', *args, **kwargs)


def print_info(*args, **kwargs):
    __cprint(*args, **kwargs)


class LockedIterator(object):
    def __init__(self, it):
        self.lock = threading.Lock()
        self.it = it.__iter__()

    def __iter__(self):
        return self

    def next(self):
        self.lock.acquire()
        try:
            return self.it.next()
        finally:
            self.lock.release()


def print_table(headers, *args, **kwargs):
    """ Print table.

    example:

    Name            Current setting     Description
    ----            ---------------     -----------
    option_name     value               description
    foo             bar                 baz
    foo             bar                 baz

    :param headers: Headers names ex.('Name, 'Current setting', 'Description')
    :param args: table values, each element representing one line ex. ('option_name', 'value', 'description), ...
    :param kwargs: 'extra_fill' space between columns, 'header_separator' character to separate headers from content
    :return:
    """
    extra_fill = kwargs.get("extra_fill", 5)
    header_separator = kwargs.get("header_separator", '-')

    if not all(map(lambda x: len(x) == len(headers), args)):
        print_error("Headers and table rows tuples should be the same length.")
        return

    def custom_len(x):
        try:
            return len(x)
        except TypeError:
            return 0

    fill = []
    headers_line = '   '
    headers_separator_line = '   '
    for idx, header in enumerate(headers):
        current_line_fill = max(len(header), *map(lambda x: custom_len(x[idx]), args)) + extra_fill
        fill.append(current_line_fill)
        headers_line = "".join((headers_line, "{header:<{fill}}".format(header=header, fill=current_line_fill)))
        headers_separator_line = "".join((
            headers_separator_line,
            '{:<{}}'.format(header_separator * len(header), current_line_fill)
        ))

    print()
    print(headers_line)
    print(headers_separator_line)
    for arg in args:
        content_line = '   '
        for idx, element in enumerate(arg):
            content_line = "".join((
                content_line,
                '{:<{}}'.format(element, fill[idx])
            ))
        print(content_line)

    print()


def sanitize_url(address):
    """Sanitize url.

    Converts address to valid HTTP url.
    """
    if address.startswith("http://") or address.startswith("https://"):
        return address
    else:
        return "http://{}".format(address)


def pprint_dict_in_order(dictionary, order=None):
    """ Pretty dict print.

    Pretty printing dictionary in specific order. (as in 'show info' command)
    Keys not mentioned in *order* parameter will be printed in random order.

    ex. pprint_dict_in_order({'name': John, 'sex': 'male', "hobby": ["rugby", "golf"]}, ('sex', 'name'))

    Sex:
    male

    Name:
    John

    Hobby:
    - rugby
    - golf

    """
    order = order or ()

    def prettyprint(title, body):
        print_info("\n{}:".format(title.capitalize()))
        if not isinstance(body, str):
            for value_element in value:
                print_info('- ', value_element)
        else:
            print_info(value)

    keys = dictionary.keys()
    for element in order:
        try:
            key = keys.pop(keys.index(element))
            value = dictionary[key]
        except (KeyError, ValueError):
            pass
        else:
            prettyprint(element, value)

    for rest_keys in keys:
        prettyprint(rest_keys, dictionary[rest_keys])


def random_text(length, alph=string.letters+string.digits):
    """ Random text generator. NOT crypto safe.
    
    Generates random text with specified length and alphabet.
    """
    return ''.join(random.choice(alph) for _ in range(length))


def http_request(method, url, **kwargs):
    """ Wrapper for 'requests' silencing exceptions a little bit. """

    try:
        return getattr(requests, method.lower())(url, **kwargs)
    except (requests.exceptions.MissingSchema, requests.exceptions.InvalidSchema):
        print_error("Invalid URL format: {}".format(url))
        return
    except requests.exceptions.ConnectionError:
        print_error("Connection error: {}".format(url))
        return
    except requests.RequestException as error:
        print_error(error)
        return
