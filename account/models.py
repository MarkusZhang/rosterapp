from uuid import uuid1

from django.db import models
from django.contrib.auth.models import User

from common.abcmodels import TimeStampedModel

class UserPreference(TimeStampedModel):
    EMAIL_NOTIFICATION=0
    SMS_NOTIFICATION=1
    notification_method=models.IntegerField(choices=(
        (EMAIL_NOTIFICATION,'email notification'),
        (SMS_NOTIFICATION,'sms notification'),
    ))
    user=models.OneToOneField(User)

    def __unicode__(self):
        return "preference of "+ self.user.username

class Manager(TimeStampedModel):
    user=models.OneToOneField(User) # we will use email as username
    name=models.CharField(max_length=200,unique=True)
    telephone=models.CharField(max_length=20)
    is_activated=models.BooleanField(default=False)

    def __unicode__(self):
        return self.name

    def add_employee_to_default_team(self,employee_user):
        teams = Team.objects.filter(head=self.user,is_default=True)
        default_team = teams[0]
        default_team.add_member(employee_user)


class Employee(TimeStampedModel):
    MALE=0
    FEMALE=1
    user=models.OneToOneField(User,null=True,blank=True) # we will use email as username
    gender=models.IntegerField(choices=(
        (MALE,'male'),
        (FEMALE,'female'),
    ),blank=True,null=True)
    name=models.CharField(max_length=200,unique=True)
    performance=models.IntegerField(default=50,null=True,blank=True) # on a scale of 0-100
    telephone=models.CharField(max_length=20,null=True,blank=True)
    on_leave=models.BooleanField(default=False)
    is_activated=models.BooleanField(default=False)

    def __unicode__(self):
        return self.name

    def get_user_id(self):
        return self.user.id

    def get_type(self):
        return "real" if self.user.is_active else "mock"

    def get_email(self):
        return self.user.email

    def get_team_ids(self):
        team_members = TeamMember.objects.filter(member=self.user)
        return [t.team.id for t in team_members]

    def get_team_names(self):
        team_members = TeamMember.objects.filter(member=self.user)
        return [t.team.name for t in team_members]

    def is_for_manager(self,manager_user):
        teams = Team.objects.filter(head=manager_user)
        if (not teams):
            return False
        for team in teams:
            if (team.is_involve_user(self.user)):
                return True
        return False


class Team(TimeStampedModel):
    name=models.CharField(max_length=250,unique=True)
    head=models.ForeignKey(User)
    is_default  = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name

    @staticmethod
    def remove_from_default_team(user):
        tms = TeamMember.objects.filter(team__is_default=True,member=user)
        if (tms):
            tms.delete()

    def is_involve_user(self,employee_user):
        return True if self.teammember_set.filter(member=employee_user) else False

    def add_member(self,user):
        TeamMember.objects.create(
            team=self,
            member=user
        )

    def get_head_name(self):
        return self.head.manager.name

    def add_member_by_user_ids(self,user_ids):
        ids_added=[]
        for id in user_ids:
            user = User.objects.get(id=id)
            if (not TeamMember.objects.filter(team=self,member=user)):
                TeamMember.objects.create(
                    team=self,
                    member=user
                )
                ids_added.append(user.id)
        return ids_added

    def remove_member_by_user_ids(self,user_ids):
        ids_deleted=[]
        for id in user_ids:
            user = User.objects.get(id=id)
            try:
                TeamMember.objects.get(team=self,member=user).delete()
                ids_deleted.append(user.id)
            except:
                pass
        return ids_deleted

class TeamMember(TimeStampedModel):
    """
    A m2m relationship table for team and employee
    """
    team=models.ForeignKey(Team)
    member=models.ForeignKey(User)

    class Meta:
        unique_together = (("team", "member"),)

    def __unicode__(self):
        return self.get_name() + " joins " + self.team.name

    def get_email(self):
        return self.member.email

    def get_name(self):
        return self.member.employee.name

    def get_team_name(self):
        return self.team.name

    def get_user_id(self):
        return self.member.id

class MemberInvitation(TimeStampedModel):
    team=models.ForeignKey(Team)
    email=models.CharField(max_length=250)
    token=models.TextField(null=True)
    accepted=models.BooleanField(default=False)

    def save(self, *args,**kwargs):
        self.token = uuid1().hex
        super(MemberInvitation,self).save(*args,**kwargs)

    def __unicode__(self):
        return "invitation for " + self.email + " to join " + self.team.name

class VerificationToken(TimeStampedModel):
    """
    For email verification
    """
    user=models.OneToOneField(User)
    token=models.CharField(max_length=250)

    def save(self, *args,**kwargs):
        self.token=uuid1().hex
        super(VerificationToken,self).save(*args,**kwargs)

    def __unicode__(self):
        return self.token
