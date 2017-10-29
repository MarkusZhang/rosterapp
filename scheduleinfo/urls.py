from django.conf.urls import patterns, include, url
from django.contrib import admin

from rest_framework import routers

from views import *

router = routers.DefaultRouter()
# router.register(r'plan', RosterPlanViewSet)
router.register(r'plan/time-slot-plan', TimeSlotPlanViewSet)

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^', include(router.urls)),

    # for manual schedule
    url(r'^schedule/create/',create_simple_schedule,name="create_simple_schedule"),
    url(r'^schedule/list/',get_schedule_list,name="get_schedule_list"),
    url(r'^schedule/view/(?P<object_id>\d+)/',get_schedule,name="get_schedule"),
    url(r'^schedule/(?P<object_id>\d+)/',manipulate_schedule,name="manipulate_schedule"),
    url(r'^slot/create/',create_slot_schedule,name="create_slot_schedule"),
    url(r'^slot/(?P<object_id>\d+)/',manipulate_slot_schedule,name="manipulate_slot_schedule"),
    url(r'^slot/view/(?P<object_id>\d+)/',view_slot_schedule,name="view_slot_schedule"),
    url(r'^slot/employee/(?P<user_id>\d+)/',get_slots_by_employee,name="get_slots_by_employee"),
    url(r'^slot/employee/',get_slots_by_employee_himself,name="get_slots_by_employee_himself"),

    # for exporting
    url(r'^calendar/',download_calendar,name="download_calendar"),
    url(r'^csv/employee/(?P<user_id>\d+)/',download_employee_slots,name="download_employee_slots"),
    url(r'^csv/timeclocked/',download_time_clocks,name="download_time_clocks"),
    url(r'^csv/scheduleslots/(?P<object_id>\d+)/',download_schedule_slots,name="download_schedule_slots"),

    # for auto schedule
    url(r'^plan/employee/add/',add_employee_for_roster,name="add_employee_for_roster"),
    url(r'^plan/employee/view/',view_employee_for_roster,name="get_employee_for_roster"),
    url(r'^plan/start-auto/',start_auto_scheduling,name="start_auto_scheduling"),
    url(r'^plan/create/',create_plan,name="create_plan"),
    url(r'^plan/list/',get_plan_list,name="get_plan_list"),
    url(r'^plan/(?P<object_id>\d+)/',manipulate_plan,name="manipulate_plan"),

    url(r'^plan/time-slot-plan/filter/(?P<object_id>\d+)/',get_slot_plan_by_plan,name="get_slot_plan_by_plan"),
)