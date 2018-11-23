from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    自定义权限，只有创建者才能编辑
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            """只读权限"""
            return True
        """读写权限"""
        return request.user and request.user.is_superuser

    def has_permission(self, request, view):
        return True


class IsProductMange(permissions.BasePermission):
    """
    是否拥有成品管理的权限
    """

    def has_permission(self, request, view):
        """类权限"""
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.is_superuser

    def has_object_permission(self, request, view, obj):
        """对象级权限"""
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        return request.user and request.is_superuser

    """先执行类型级别权限，再执行对象级别权限  has_permission -> has_object_permission"""
