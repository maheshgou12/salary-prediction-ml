# FairSalary AI - Password Utilities
from passlib.context import CryptContext

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain text password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_strength(password: str) -> dict:
    """Check password strength and return feedback."""
    feedback = []
    score = 0

    if len(password) >= 8:
        score += 1
    else:
        feedback.append("At least 8 characters")

    if len(password) >= 12:
        score += 1

    if any(c.isupper() for c in password):
        score += 1
    else:
        feedback.append("At least one uppercase letter")

    if any(c.islower() for c in password):
        score += 1
    else:
        feedback.append("At least one lowercase letter")

    if any(c.isdigit() for c in password):
        score += 1
    else:
        feedback.append("At least one digit")

    if any(not c.isalnum() for c in password):
        score += 1
    else:
        feedback.append("At least one special character")

    strength_labels = {
        0: "Very Weak",
        1: "Very Weak",
        2: "Weak",
        3: "Fair",
        4: "Good",
        5: "Strong",
        6: "Very Strong",
    }

    return {
        "score": score,
        "max_score": 6,
        "strength": strength_labels.get(score, "Unknown"),
        "feedback": feedback if feedback else ["Strong password!"]
    }