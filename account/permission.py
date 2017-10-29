from rest_framework import permissions

from models import Manager,Employee

class GlobalPermission(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        permitted= super(GlobalPermission,self).has_permission(request,view)
        if (not permitted):
            return False

        user=request.user
        # permit staff
        if (user.is_staff):
            return True
        # permit activated manager
        try:
            manager=Manager.objects.get(user=user)
            if (manager.is_activated):
                return True
        except:
            pass
        # permit activated employee
        try:
            employee=Employee.objects.get(user=user)
            if (employee.is_activated):
                return True
        except:
            pass

        return False