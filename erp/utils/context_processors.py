def branch_context(request):
    return {'current_branch': getattr(request, 'branch', None)}