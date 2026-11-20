def user_info(request):
    is_admin = False
    is_client = False
    is_worker = False

    if request.user.is_authenticated:
        is_admin = request.user.is_superuser  # Gli amministratori sono superusers
        is_client = request.user.role == 'client'
        is_worker = request.user.role == 'maintenance_worker'

    return {
        'user_is_admin': is_admin,
        'user_is_client': is_client,
        'user_is_worker': is_worker,
    }
