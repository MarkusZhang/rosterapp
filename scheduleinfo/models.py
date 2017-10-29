from django.db import models
from django.contrib.auth.models import User

from common.abcmodels import TimeStampedModel
from account.models import Employee

class EmployeeOccupiedTimeSlot(TimeStampedModel):
    """
    Record employee's unavailable time slots for auto scheduling
    """
    employee=models.ForeignKey(User)
    reason = models.CharField(max_length=250)
    start_time=models.DateTimeField()
    end_time=models.DateTimeField()

    def __unicode__(self):
        return self.employee.name + " : " + str(self.start_time) + " ~ " + str(self.end_time)


class Schedule(TimeStampedModel):
    """
        also named schedule
    """
    manager = models.ForeignKey(User)
    name=models.CharField(max_length=250)
    description=models.TextField(null=True)
    is_finished=models.BooleanField(default=False)
    is_auto_roster=models.BooleanField(default=False)

    def __unicode__(self):
        return self.name


class TimeSlotSchedule(TimeStampedModel):
    schedule=models.ForeignKey(Schedule,related_name="slots")
    start_time=models.DateTimeField()
    end_time=models.DateTimeField()
    location=models.TextField(null=True,blank=True)
    description=models.TextField(null=True,blank=True)

    def __unicode__(self):
        return str(self.schedule) +" : "+ str(self.start_time) + "~" + str(self.end_time)

    def get_schedule_name(self):
        return self.schedule.name

    @staticmethod
    def quick_create_schedule(start_time,end_time,description,employee_users,schedule):
        slot_schedule = TimeSlotSchedule.objects.create(
            start_time=start_time,
            end_time=end_time,
            description=description,
            schedule=schedule
        )
        for user in employee_users:
            TimeSlotScheduleEmployee.objects.create(
                time_slot_schedule = slot_schedule,
                employee = user
            )
        return slot_schedule

    def clear_scheduled_employees(self):
        self.timeslotscheduleemployee_set.all().delete()

    def get_employee_user_ids(self):
        return [a.employee.id for a in self.timeslotscheduleemployee_set.all()]

    def get_employee_names(self):
        names= []
        tss_employees = self.timeslotscheduleemployee_set.all()
        for tsse in tss_employees:
            user= tsse.employee
            try:
                names.append(user.employee.name)
            except:
                pass
        return names

    def is_involve_user(self,user):
        return True if self.timeslotscheduleemployee_set.filter(employee=user) else False

class TimeSlotScheduleEmployee(TimeStampedModel):
    """
    a m2m relation table
    """
    time_slot_schedule=models.ForeignKey(TimeSlotSchedule)
    employee=models.ForeignKey(User)

    def __unicode__(self):
        return self.employee.username + " scheduled at " + str(self.time_slot_schedule)

class SwapTimeSlotRequest(TimeStampedModel):
    swap_from= models.ForeignKey(TimeSlotSchedule,related_name="swap_from_request")
    swap_to=models.ForeignKey(TimeSlotSchedule,related_name="swap_to_request")
    status=models.IntegerField(choices=(
        (0,'pending'),
        (1,'approved'),
        (2,'rejected'),
    ))

    def __unicode__(self):
        return "Request to swap from " + str(self.swap_from) + " to " + str(self.swap_to)


class RosterPlan(TimeStampedModel):
    schedule=models.OneToOneField(Schedule)
    status=models.IntegerField(choices=(
        (0,'draft'),
        (1,'done'),
    ),default=1)

    def __unicode__(self):
        return self.schedule.name

    def get_description(self):
        return self.schedule.description

    def get_name(self):
        return self.schedule.name

    def get_involved_employees(self):
        rp_employees=self.rosterplanemployee_set.all()
        if (rp_employees):
            return [a.employee for a in rp_employees]
        else:
            return [e.user for e in Employee.objects.all()]

    def get_time_slot_plans(self):
        return self.timeslotrosterplan_set.all()

class RosterPlanEmployee(TimeStampedModel):
    employee=models.ForeignKey(User)
    roster_plan=models.ForeignKey(RosterPlan)

    def __unicode__(self):
        return self.employee.username + " involved in " + self.roster_plan.name

    def get_name(self):
        try:
            return self.employee.employee.name
        except:
            return "N.A."


class TimeSlotRosterPlan(TimeStampedModel):
    MALE_ONLY=0
    FEMALE_ONLY=1
    PRIORITY_CHOICES=(
        (1,"Very low"),
        (2,"Low"),
        (3,"Medium"),
        (4,"High"),
        (5,"Very high"),
    )
    roster_plan=models.ForeignKey(RosterPlan)
    start_time=models.DateTimeField()
    end_time=models.DateTimeField()
    requirement=models.IntegerField(choices=(
        (MALE_ONLY,'male only'),
        (FEMALE_ONLY,'female only'),
    ),null=True) # special requirement for the slot, optional
    number_of_people=models.IntegerField()
    location=models.TextField(blank=True,null=True)
    priority=models.IntegerField(choices=PRIORITY_CHOICES,default=3) # the larger the number, the higher the priority
    task_description=models.TextField(blank=True,null=True)

    def __unicode__(self):
        return str(self.start_time) + " ~ " + str(self.end_time)

    def get_number_of_people(self):
        return self.number_of_people

    def get_description(self):
        return self.task_description