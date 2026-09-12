"""Deliberately buggy sample file. Contains exactly 6 intended issues,
one for each rule, and nothing else that should trigger a false positive."""


def load_config(path):
    try:
        return open(path).read()
    except:  # BUG 1 (ML001): bare except
        return None


def is_missing(value):
    if value == None:  # BUG 2 (ML002): should be `is None`
        return True
    return False


def classify(n):
    if n < 0:
        return "negative"
        print("unreachable")  # BUG 3 (ML003): dead code after return
    return "non-negative"


def compute_total(items):
    total = 0
    unused = 42  # BUG 4 (ML004): assigned, never used
    for item in items:
        total += item
    return total


def make_counter():
    count = 0
    print(f"starting count at {count}")

    def increment():
        count = count + 1  # BUG 5 (ML005): shadows outer `count`
        return count

    return increment


def greet(name):
    message = f"Hello, {greeting}"  # BUG 6 (ML006): `greeting` used before assignment
    greeting = name
    return message
