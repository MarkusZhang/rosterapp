from django.contrib import admin

from models import *

admin.site.register(Manager)
admin.site.register(Employee)
admin.site.register(Team)
admin.site.register(TeamMember)
admin.site.register(UserPreference)
admin.site.register(MemberInvitation)
admin.site.register(VerificationToken)