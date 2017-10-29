from django.contrib import admin

from models import *


admin.site.register(RosterPlan)
admin.site.register(RosterPlanEmployee)
admin.site.register(EmployeeOccupiedTimeSlot)
admin.site.register(TimeSlotRosterPlan)
admin.site.register(Schedule)
admin.site.register(TimeSlotSchedule)
admin.site.register(TimeSlotScheduleEmployee)
admin.site.register(SwapTimeSlotRequest)