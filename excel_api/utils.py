from .models import ApiUser


def is_valid_key(key):
    user = ApiUser.objects.filter(key=key)
    if user.exists():
        return True, user[0]
    else:
        return False, None


