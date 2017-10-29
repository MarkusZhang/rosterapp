from django.conf.urls import patterns, include, url
from django.contrib import admin

from rest_framework import routers

from views import *

router = routers.DefaultRouter()
router.register(r'team', TeamViewSet)
router.register(r'employee', EmployeeViewSet)

urlpatterns = patterns('',
    url(r'^manager/create/', create_user,{"type":"manager"},name="create_manager"),
    url(r'^employee/create/', create_user,{"type":"employee"},name="create_employee"),
    url(r'^verify/(?P<verification_token>[-\w]*)/', verify_email,name="verify_email"),
    url(r'^login/', login,name="login"),
    url(r'^team/invite-member/',invite_team_member,name="invite_team_member"),
    url(r'^team/(?P<team_name>[-\w]*)/member/',get_team_member,name="get_team_member"),
    url(r'^team/invitation/verify/(?P<token>[-\w]*)',verify_invitation_token,name="verify_invitation_token"),
    url(r'^team/withdraw/',withdraw_team,name="withdraw_team"),
    url(r'^profile/view/',view_profile,name="view_profile"),
    url(r'^profile/set/',set_profile,name="set_profile"),

    url(r'^mock-employee/$',create_mock_employee,name="create_mock_employee"),
    url(r'^mock-employee/(?P<object_id>\d+)/$',manipulate_mock_employee,name="manipulate_mock_employee"),
    url(r'^team/add-member/',add_team_member,name="add_team_member"),
    url(r'^team/remove-member/',remove_team_member,name="remove_team_member"),

    url(r'^employee/(?P<object_id>\d+)/$',manipulate_employee,name="manipulate_employee"),
    url(r'^', include(router.urls)),
)
