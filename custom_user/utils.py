from rest_framework_simplejwt.tokens import RefreshToken

def custom_preprocessing_hook(endpoints):
    excluded_paths = [
        '/api/user/users/',
        '/api/user/users/{id}/',
        '/api/user/users/resend_activation/',
        '/api/user/users/reset_email/',
        '/api/user/users/reset_email_confirm/',
        '/api/user/users/reset_password/',
        '/api/user/users/reset_password_confirm/',
        '/api/user/users/set_password/',
        '/api/user/users/set_email/',
        '/api/user/users/activation/',
    ]

    filtered = []
    for (path, path_regex, method, callback) in endpoints:
        if path not in excluded_paths:
            filtered.append((path, path_regex, method, callback))

    return filtered


def get_tokens_for_user(user, device_hardware=None):
    refresh = RefreshToken.for_user(user)

    if device_hardware:
        refresh['device_hardware'] = device_hardware

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


def get_device_from_token(token):
    from rest_framework_simplejwt.tokens import AccessToken

    try:
        access_token = AccessToken(token)
        device_hardware = access_token.get('device_hardware')
        user_id = access_token.get('user_id')
        return {
            'user_id': user_id,
            'device_hardware': device_hardware
        }
    except Exception as e:
        return None
