from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Admins can write (and read).
    Operator can only read.
    """

    def has_permission(self, request, view):
        """
        Any user that wants to read, can read.
        For this, everyone can use GET.
        Any user that wants to use POST, PUT or DELETE must be:
        - Authenticated
        - An admin
        """
        # SAFE_METHODS -> GET, HEAD, OPTIONS
        # Part for all the users to use GET
        if request.method in permissions.SAFE_METHODS:
            return True
        return (
                request.user and
                # User it authenticated
                request.user.is_authenticated and
                # And is an admin
                request.user.groups.filter(name="admin").exists()
        )