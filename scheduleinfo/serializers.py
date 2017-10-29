from rest_framework import serializers

from common.serializers import IdModelSerializer

from models import *

class RosterPlanSerializer(IdModelSerializer):
    name = serializers.CharField(source="get_name")
    description = serializers.CharField(source="get_description")

    class Meta:
        model = RosterPlan
        fields = ['id','name','description']

class TimeSlotPlanSerializer(IdModelSerializer):
    class Meta:
        model = TimeSlotRosterPlan

class RosterPlanEmployeeSerializer(serializers.ModelSerializer):
    id=serializers.IntegerField(source='employee.id')
    name=serializers.CharField(source="get_name")
    email=serializers.EmailField(source='employee.email')

    class Meta:
        model = RosterPlanEmployee
        fields = ['id','name','email']

class ScheduleSerializer(IdModelSerializer):
    class Meta:
        model = Schedule


class TimeSlotScheduleSerializer(IdModelSerializer):
    employee_id = serializers.ListField(source="get_employee_user_ids",read_only=True)
    employee_name = serializers.ListField(source="get_employee_names",read_only=True)
    schedule_name = serializers.CharField(source="get_schedule_name",read_only=True)

    class Meta:
        model = TimeSlotSchedule
        fields = ['start_time','end_time','schedule','employee_id','location','description','schedule','employee_name','schedule_name']


class ScheduleDetailSerializer(IdModelSerializer):
    slots = TimeSlotScheduleSerializer(many=True,read_only=True)

    class Meta:
        model = Schedule
        fields = ['manager','name','description','is_finished','is_auto_roster','slots']


