import random
import string
import unicodedata

FIRST_NAMES = [
    "John", "Jane", "Alex", "Chris", "Taylor", "Jordan", "Sam", "Casey",
    "Morgan", "Riley", "Avery", "Skyler", "Jamie", "Drew", "Quinn",
]

LAST_NAMES = [
    "Nguyen", "Tran", "Le", "Pham", "Hoang", "Do", "Vo", "Huynh",
    "Smith", "Johnson", "Brown", "Taylor", "Anderson", "Thomas",
]


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_str = normalized.encode("ascii", "ignore").decode("ascii")
    clean = ''.join(ch for ch in ascii_str.lower() if ch.isalnum())
    return clean


def generate_name() -> tuple[str, str]:
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    return first, last


def generate_username(first: str, last: str) -> str:
    base = _slugify(first) + _slugify(last)
    # Optionally insert a dot
    if random.random() < 0.4 and len(base) > 6:
        split = random.randint(3, min(6, len(base) - 3))
        base = base[:split] + "." + base[split:]
    suffix = str(random.randint(100, 9999))
    return (base + suffix)[:30]


def generate_password(length: int = 14) -> str:
    upper = string.ascii_uppercase
    lower = string.ascii_lowercase
    digits = string.digits
    symbols = "!@#$%^&*()-_=+"  # keep browser-safe symbols
    all_chars = upper + lower + digits + symbols
    # Ensure complexity
    password = [
        random.choice(upper),
        random.choice(lower),
        random.choice(digits),
        random.choice(symbols),
    ]
    password += [random.choice(all_chars) for _ in range(max(4, length - 4))]
    random.shuffle(password)
    return ''.join(password) 