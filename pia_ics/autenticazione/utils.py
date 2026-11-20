from django.contrib.auth import get_user_model

def authenticate_with_email(email=None, password=None):
    User = get_user_model()
    try:
        user = User.objects.get(email=email)
        if user.check_password(password):
            return user
    except User.DoesNotExist:
        return None