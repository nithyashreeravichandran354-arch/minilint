"""Equivalent to samples/buggy.py, but with every issue fixed. Linting
this file should produce zero diagnostics."""


def load_config(path):
    try:
        return open(path).read()
    except OSError:
        return None


def is_missing(value):
    if value is None:
        return True
    return False


def classify(n):
    if n < 0:
        return "negative"
    return "non-negative"


def compute_total(items):
    total = 0
    for item in items:
        total += item
    return total


def make_counter():
    count = 0

    def increment():
        nonlocal count
        count = count + 1
        return count

    return increment


def greet(name):
    greeting = name
    message = f"Hello, {greeting}"
    return message
