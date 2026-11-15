from rest_framework.permissions import BasePermission


class IsCreator(BasePermission):
    def has_object_permission(self, request, view, obj):
        """Allow access to a quiz object only for its creator.

        Args:
            request: The incoming request containing the authenticated user.
            view: The view that handles the request.
            obj: The quiz object the request refers to.

        Returns:
            bool: True if the user is the creator of the object (for GET, PATCH,
            PUT and DELETE) or the method is not restricted, otherwise False.
        """
    
        if request.method in ("GET", "PATCH", "PUT", "DELETE"):
            return obj.creator == request.user

        return True
