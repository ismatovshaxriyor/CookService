
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