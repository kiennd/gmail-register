import random
import string
import unicodedata

FIRST_NAMES = [
    "An", "Anh", "Bình", "Chi", "Dũng", "Duy", "Giang", "Hà", "Hải", "Hằng",
    "Hiếu", "Hoa", "Hòa", "Hồng", "Hưng", "Huy", "Khánh", "Kiên", "Lan", "Linh",
    "Loan", "Long", "Mai", "Minh", "My", "Nam", "Nga", "Ngân", "Ngọc", "Nhung",
    "Phong", "Phúc", "Phương", "Quang", "Quyên", "Sơn", "Thảo", "Thắng", "Thành",
    "Thịnh", "Thu", "Thủy", "Trang", "Trí", "Trinh", "Trọng", "Tú", "Tuấn", "Tùng",
    "Tuyết", "Uyên", "Vân", "Vinh", "Vy",
]

LAST_NAMES = [
    "Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng",
    "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý",
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
    # Longer random numeric suffix for better uniqueness
    suffix_length = random.randint(6, 9)
    suffix = ''.join(random.choices(string.digits, k=suffix_length))
    return (base + suffix)[:30]


def generate_password(length: int = 10) -> str:
    upper = string.ascii_uppercase
    lower = string.ascii_lowercase
    digits = string.digits
    symbols = "@"  # keep browser-safe symbols
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


def ensure_password_has_special(password: str) -> str:
    symbols = "@"
    if any(ch in symbols for ch in password):
        return password
    if not password:
        return generate_password()
    insert_at = random.randint(0, len(password))
    return password[:insert_at] + random.choice(symbols) + password[insert_at:]