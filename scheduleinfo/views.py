from threading import Thread
import sched,time

from django.db import transaction
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes,authentication_classes
from rest_framework.authentication import BasicAuthentication,TokenAuthentication

import rosterengine
from roster.settings import EMAIL_HOST_USER
from serializers import *
from exporters import  *

class RosterPlanViewSet(viewsets.ModelViewSet):
    queryset = RosterPlan.objects.all()
    serializer_class = RosterPlanSerializer
    authentication_classes=(TokenAuthentication,)

class TimeSlotPlanViewSet(viewsets.ModelViewSet):
    queryset = TimeSlotRosterPlan.objects.all()
    serializer_class = TimeSlotPlanSerializer
    authentication_classes=(TokenAuthentication,)

@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
def add_employee_for_roster(request):
    roster_plan_id=request.data.get('roster_plan_id')
    roster_plan=get_object_or_404(RosterPlan,id=roster_plan_id)
    employee_id_list=request.data.getlist('selected_employees')
    return_data=[]
    for id in employee_id_list:
        obj = RosterPlanEmployee.objects.create(
            employee=get_object_or_404(User,id=id),
            roster_plan=roster_plan
        )
        return_data.append(RosterPlanEmployeeSerializer(obj).data)

    return Response(data=return_data,status=status.HTTP_200_OK)

@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
def view_employee_for_roster(request):
    roster_plan_id=request.data.get('roster_plan_id')
    roster_plan=get_object_or_404(RosterPlan,id=roster_plan_id)
    objs = RosterPlanEmployee.objects.filter(roster_plan=roster_plan)
    return_data=[RosterPlanEmployeeSerializer(obj).data for obj in objs]
    return Response(data=return_data,status=status.HTTP_200_OK)

@transaction.atomic
@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
def start_auto_scheduling(request):
    def send_emails(users,roster_plan):
        email_content= "You have been added in a new roster plan:\n"+roster_plan.get_description() + "\n" + "Please go to the website to indicate your time slots"
        email_title= "Indicate your available time slots"
        email_host = EMAIL_HOST_USER
        mailing_list=[u.email for u in users]
        send_mail(subject=email_title,message=email_content,from_email=email_host,recipient_list=mailing_list)

    roster_plan_id=request.data.get('roster_plan_id')
    roster_plan=get_object_or_404(RosterPlan,id=roster_plan_id)
    schedule = roster_plan.schedule
    employee_users=roster_plan.get_involved_employees()
    # email the users
    thread=Thread(target=send_emails,args=(employee_users,roster_plan))
    thread.start()
    # start doing auto-scheduling
    scheduler = sched.scheduler(time.time, time.sleep)
    # TODO: change the delay
    scheduler.enter(5, 1, conduct_auto_scheduling, (roster_plan.get_time_slot_plans(),employee_users,schedule))
    scheduler.run()
    #conduct_auto_scheduling(roster_plan.get_time_slot_plans(),employee_users,schedule)

    return Response(data={'msg':'auto scheduling has started!'},status=status.HTTP_200_OK)

def conduct_auto_scheduling(time_slot_plans,employee_users,schedule):
    # run roster engine
    time_slot_results=rosterengine.do_roster(time_slot_plans=time_slot_plans,employee_users=employee_users)
    # construct a roster result
    for result in time_slot_results:
        slot_roster_plan = TimeSlotRosterPlan.objects.get(id=result.keys()[0])
        employees_chosen = result.values()[0]
        TimeSlotSchedule.quick_create_schedule(start_time=slot_roster_plan.start_time,
                                               end_time=slot_roster_plan.end_time,
                                               description=slot_roster_plan.get_description(),
                                               employee_users=employees_chosen,
                                               schedule=schedule)
    schedule.is_finished=True
    schedule.save()
    # store notification
    def send_emails(users,roster_plan):
        email_content= "Roster plan: "+roster_plan.get_description() + "has been auto scheduled. \n Please go to the website to see the result"
        email_title= "New schedule generated"
        email_host = EMAIL_HOST_USER
        mailing_list=[u.email for u in users]
        send_mail(subject=email_title,message=email_content,from_email=email_host,recipient_list=mailing_list)

    thread=Thread(target=send_emails,args=(employee_users,time_slot_plans[0].roster_plan))
    thread.start()

@transaction.atomic
@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
def create_simple_schedule(request):
    title = request.data['name']
    schedule = Schedule.objects.create(
        name = title,
        manager = request.user,
        is_finished=True
    )
    return Response(data=ScheduleSerializer(schedule).data,status=status.HTTP_200_OK)

@transaction.atomic
@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
def create_slot_schedule(request):
    serializer = TimeSlotScheduleSerializer(data=request.data)
    if (serializer.is_valid()):
        time_slot_schedule = serializer.save()
        return Response(data=TimeSlotScheduleSerializer(time_slot_schedule).data,status=status.HTTP_200_OK)
    else:
        return Response(data={'msg':'data not valid'},status=status.HTTP_400_BAD_REQUEST)

@transaction.atomic
@api_view(['POST','DELETE','GET'])
@authentication_classes((TokenAuthentication,))
def manipulate_slot_schedule(request,object_id):
    time_schedule = get_object_or_404(TimeSlotSchedule,id=object_id)
    if (request.method=="DELETE"):
        time_schedule.delete()
        return Response(data={},status=status.HTTP_204_NO_CONTENT)
    elif (request.method=="GET"):
        return Response(data=TimeSlotScheduleSerializer(time_schedule).data,status=status.HTTP_200_OK)
    elif (request.method=="POST"):
        serializer = TimeSlotScheduleSerializer(data=request.data,instance=time_schedule,partial=True)
        if (serializer.is_valid()):
            updated_time_schedule = serializer.save()
            # clear employee m2m
            updated_time_schedule.clear_scheduled_employees()
            # save employee m2m
            employee_user_ids = request.data['employee_id'][0]
            for user_id in employee_user_ids:
                employee_user = get_object_or_404(User,id=user_id)
                TimeSlotScheduleEmployee.objects.create(
                    time_slot_schedule = updated_time_schedule,
                    employee = employee_user
                )
            return Response(data=TimeSlotScheduleSerializer(updated_time_schedule).data,status=status.HTTP_200_OK)
        else:
            return Response(data={'msg':'data not valid'},status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@authentication_classes((TokenAuthentication,))
def view_slot_schedule(request,object_id):
    time_schedule = get_object_or_404(TimeSlotSchedule,id=object_id)
    return Response(data=TimeSlotScheduleSerializer(time_schedule).data,status=status.HTTP_200_OK)

@api_view(['GET'])
@authentication_classes((TokenAuthentication,))
def get_slots_by_employee(request,user_id):
    time_schedules = [TimeSlotScheduleSerializer(t).data for t in TimeSlotSchedule.objects.all() if t.is_involve_user(get_object_or_404(User,id=user_id))]
    return Response(data=time_schedules,status=status.HTTP_200_OK)

@api_view(['GET'])
@authentication_classes((TokenAuthentication,))
def get_schedule_list(request):
    schedules = Schedule.objects.filter(is_finished=True,manager=request.user)
    return Response(data=[ScheduleSerializer(a).data for a in schedules],status=status.HTTP_200_OK)


@api_view(['GET'])
@authentication_classes((TokenAuthentication,))
def get_schedule(request,object_id):
    schedule = get_object_or_404(Schedule,id=object_id,manager=request.user)
    return Response(data=ScheduleDetailSerializer(schedule).data,status=status.HTTP_200_OK)

@transaction.atomic
@api_view(['DELETE','POST'])
@authentication_classes((TokenAuthentication,))
def manipulate_schedule(request,object_id):
    schedule = get_object_or_404(Schedule,id=object_id)
    if (schedule.manager != request.user):
        return Response(data={},status=status.HTTP_401_UNAUTHORIZED)
    if (request.method == "DELETE"):
        schedule.delete()
        return Response(data={},status=status.HTTP_204_NO_CONTENT)
    elif (request.method == "POST"):
        serializer = ScheduleSerializer(data=request.data,instance=schedule,partial=True)
        if (serializer.is_valid()):
            updated_schedule = serializer.save()
            return Response(data=ScheduleSerializer(updated_schedule).data,status=status.HTTP_200_OK)
        else:
            return Response(data={'msg':'data not valid'},status=status.HTTP_400_BAD_REQUEST)


@transaction.atomic
@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
def create_plan(request):
    name = request.data['name']
    description = request.data['description']
    schedule = Schedule.objects.create(
        name = name,
        description = description,
        manager = request.user,
        is_auto_roster = True
    )
    plan = RosterPlan.objects.create(
        schedule = schedule
    )
    return Response(data=RosterPlanSerializer(plan).data,status=status.HTTP_200_OK)


@transaction.atomic
@api_view(['DELETE','POST'])
@authentication_classes((TokenAuthentication,))
def manipulate_plan(request,object_id):
    plan = get_object_or_404(RosterPlan,id=object_id)
    schedule = plan.schedule
    if (request.method == "DELETE"):
        plan.delete()
        return Response(data={},status=status.HTTP_204_NO_CONTENT)
    elif (request.method == "POST"):
        name = request.data.get('name')
        description = request.data.get('description')
        if (name):
            schedule.name = name
        if (description):
            schedule.description = description
        schedule.save()
        return Response(data=RosterPlanSerializer(plan).data,status=status.HTTP_200_OK)
    elif (request.method == "GET"):
        return Response(data=RosterPlanSerializer(plan).data,status=status.HTTP_200_OK)


@api_view(['GET'])
@authentication_classes((TokenAuthentication,))
def get_plan_list(request):
    plans = RosterPlan.objects.filter(schedule__manager=request.user)
    return Response(data=[RosterPlanSerializer(p).data for p in plans],status=status.HTTP_200_OK)

@api_view(['GET'])
@authentication_classes((TokenAuthentication,))
def get_slot_plan_by_plan(request,object_id):
    plan = get_object_or_404(RosterPlan,id=object_id)
    slot_plans = plan.timeslotrosterplan_set.all()
    return Response(data=[TimeSlotPlanSerializer(a).data for a in slot_plans],status=status.HTTP_200_OK)

#======================================================
#=================export functions=====================

@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
def download_calendar(request):
    start_month = request.data['start_month']
    end_month = request.data['end_month']
    exporter = ScheduleCalendarExporter(data=Schedule.objects.all())
    return exporter.render_to_pdf_response()


@api_view(['GET'])
@authentication_classes((TokenAuthentication,))
def download_employee_slots(request,user_id):
    user = get_object_or_404(User,id=user_id)
    slot_schedules = TimeSlotSchedule.objects.all()
    user_slots = [ss for ss in slot_schedules if ss.is_involve_user(user)]
    exporter = EmployeeSlotTableExporter(data=user_slots)
    return exporter.render_to_csv_response()

@api_view(['GET'])
@authentication_classes((TokenAuthentication,))
def download_time_clocks(request):
    employees = Employee.objects.all()
    exporter = TimeClockTableExporter(data=employees)
    return exporter.render_to_csv_response()

@api_view(['GET'])
@authentication_classes((TokenAuthentication,))
def download_schedule_slots(request,object_id):
    exporter = ScheduleSlotTableExporter(data=[])
    return exporter.render_to_csv_response()


@api_view(['GET'])
@authentication_classes((TokenAuthentication,))
def get_slots_by_employee_himself(request):
    user = request.user
    try:
        filtered_schedules = [t for t in TimeSlotSchedule.objects.all() if t.is_involve_user(user)]
    except Exception as e:
        pass
    return Response(data=[TimeSlotScheduleSerializer(t).data for t in filtered_schedules],status=status.HTTP_200_OK)