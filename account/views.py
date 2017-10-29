import uuid

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt

from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes,authentication_classes
from rest_framework.authentication import BasicAuthentication,TokenAuthentication
from rest_framework.views import APIView

from roster.settings import EMAIL_HOST_USER
from common.utils import from_querydict_to_dict

from models import MemberInvitation,TeamMember
from serializers import *

@api_view(['POST'])
@authentication_classes((BasicAuthentication,))
@permission_classes((AllowAny,))
def create_user(request,type):
    if (type=="manager"):
        user_serializer = CreateManagerSerializer(data=request.data)
    else:
        user_serializer = CreateEmployeeSerializer(data=request.data)
    # validate post data
    if (not user_serializer.is_valid()):
        return Response(data=user_serializer.errors,status=status.HTTP_403_FORBIDDEN)
    # create the user

    user,token_key=user_serializer.save()

    # create default team for manager
    if (type=="manager"):
        Team.objects.create(
            head=user,
            is_default=True,
            name=user.manager.name + "-default-team"
        )
    user = authenticate(username=request.data['email'],password=request.data['password'])
    return Response(data={'token':token_key,'id':user.id},status=status.HTTP_201_CREATED)


@transaction.atomic
@api_view(['GET'])
@permission_classes((AllowAny,))
def verify_email(request,verification_token):
    v_token=get_object_or_404(VerificationToken,token=verification_token)
    user=v_token.user
    if (hasattr(user,"manager")):
        user.manager.is_activated = True
        user.manager.save()
    elif (hasattr(user,"employee")):
        user.employee.is_activated = True
        user.employee.save()
    else:
        return Response(data={"msg":"Invalid token"},status=status.HTTP_400_BAD_REQUEST)

    return Response(data={"msg":"Your email has been verified"},status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes((BasicAuthentication,))
@permission_classes((AllowAny,))
def login(request):
    user=request.user
    if (not user.is_authenticated()):
        user = authenticate(username=request.data['username'],password=request.data['password'])
    if (not user):
        return Response(data={'msg':'username or password not correct'},status=status.HTTP_401_UNAUTHORIZED)
    # generate a new auth token
    try:
        token = Token.objects.get(user=user)
        token.delete()
    except:
        pass
    token = Token.objects.create(user=user)
    token.save()

    # successful response
    data = {
        "token": token.key
    }
    return Response(data, status=status.HTTP_200_OK)

@api_view(['GET'])
@authentication_classes((BasicAuthentication,))
@permission_classes((AllowAny,))
def logout(request):
    try:
        token = Token.objects.get(user=request.user)
        token.delete()
    except Token.DoesNotExist:
        pass
    return Response({"msg":"You have logged out"}, status=status.HTTP_200_OK)

@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
def invite_team_member(request):
    team = get_object_or_404(Team,name=request.data["team"])
    emails = request.data.getlist("emails")
    for email in emails:
        invitation= MemberInvitation.objects.create(
            team= team,
            email=email,
        )
        send_mail("Invitation to join team",
                  "Click on the following link to join:" +invitation.token,
                  EMAIL_HOST_USER,
                  [email])
    return Response({"msg":"Invitations have been sent"},status=status.HTTP_200_OK)

class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    authentication_classes=(TokenAuthentication,)

    def get_queryset(self):
        manager_user = self.request.user
        return Team.objects.filter(head=manager_user)

    def create(self, request, *args, **kwargs):
        team_name=request.data['name']
        if (not hasattr(request.user,'manager')):
            return Response(data={"msg":"You are not a manager, so you cannot create team"},status=status.HTTP_400_BAD_REQUEST)
        team_head=request.user

        team= Team.objects.create(
            name=team_name,
            head=team_head
        )
        return Response(data=TeamSerializer(team).data,status=status.HTTP_201_CREATED)

@api_view(['GET'])
@authentication_classes((TokenAuthentication,))
def get_team_member(request,team_name):
    t_members=TeamMember.objects.filter(team__name=team_name)
    data=[TeamMemberSerializer(a).data for a in t_members]
    return Response(data=data,status=status.HTTP_200_OK)

@api_view(['GET'])
# @authentication_classes((TokenAuthentication,))
def verify_invitation_token(request,token):
    try:
        invitation=MemberInvitation.objects.get(token=token,accepted=False)
        invitation.accepted=True
        invitation.save()
        return Response(data={'email':invitation.email,'team':invitation.team.name},status=status.HTTP_200_OK)
    except:
        return Response(data={"msg":"Invalid invitation token"},status=status.HTTP_400_BAD_REQUEST)

@transaction.atomic
@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
def withdraw_team(request):
    team_name=request.data['team']
    reason=request.data.get("reason","")
    try:
        member=TeamMember.objects.get(team__name=team_name,member__user=request.user)
        member.delete()
        return Response(data={'msg':'you have withdrawn from the team: ' + team_name},status=status.HTTP_200_OK)
    except:
        return Response(data={'msg':'Unsuccessful'},status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@authentication_classes((TokenAuthentication,))
def view_profile(request):
    user=request.user
    if (hasattr(user,'employee')):
        profile_data=EmployeeProfileSerializer(user.employee).data
    elif(hasattr(user,'manager')):
        profile_data=ManagerProfileSerializer(user.manager).data
    else:
        return Response(data={'msg':"No profile"},status=status.HTTP_400_BAD_REQUEST)
    return Response(data=profile_data,status=status.HTTP_200_OK)

@transaction.atomic
@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
def set_profile(request):
    user=request.user
    if (hasattr(user,'employee')):
        profile=user.employee
        profile.on_leave = request.data['on_leave']
        profile.telephone = request.data['telephone']
        profile.save()
    elif(hasattr(user,'manager')):
        profile=user.employee
        profile.telephone = request.data['telephone']
    else:
        return Response(data={'msg':"No profile"},status=status.HTTP_400_BAD_REQUEST)
    return Response(data={'msg':'Profile has been updated'},status=status.HTTP_200_OK)

class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeProfileSerializer
    authentication_classes=(TokenAuthentication,)

    def get_queryset(self):
        user = self.request.user
        employees = [e for e in Employee.objects.all() if e.is_for_manager(user)]
        return employees


@transaction.atomic
@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
def create_mock_employee(request):
    def generate_random_email():
        email = uuid.uuid4().hex[:5] + "@mock.com"
        while (User.objects.filter(email=email)):
            email = uuid.uuid4().hex[:5] + "@mock.com"
        return email

    name=request.data["name"]
    email=request.data.get("email",generate_random_email())
    manager_user=request.user
    # create an inactive user
    user= User.objects.create(
        username=email,
        email=email,
        password="11111",
        is_active=False
    )
    employee= Employee.objects.create(
        user=user,
        name=name,
        is_activated=True
    )
    manager_user.manager.add_employee_to_default_team(user)
    return_data={'name':name,'email':email,'id':user.id}
    return Response(data=return_data,status=status.HTTP_200_OK)

@transaction.atomic
@api_view(['POST','DELETE'])
@authentication_classes((TokenAuthentication,))
def manipulate_mock_employee(request,object_id):
    user = get_object_or_404(User,id=object_id)
    if request.method == "DELETE":
        try:
            user.employee.delete()
        except:
            pass
        user.delete()
        return Response(data={},status=status.HTTP_204_NO_CONTENT)
    elif request.method == "POST":
        name = request.data.get('name')
        email=request.data.get('email')
        if (email):
            user.username = email
            user.email=email
            user.save()
        if (name):
            try:
                user.employee.name=name
                user.employee.save()
            except:
                pass
        return_data= {'name':user.employee.name,'email':user.email,'id':user.id}
        return Response(data=return_data,status=status.HTTP_200_OK)

@transaction.atomic
@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
def add_team_member(request):
    team_name=request.data['team']
    ids = request.data['ids']
    id=ids[0]
    employee_user = get_object_or_404(User,id=id)
    team = get_object_or_404(Team,name=team_name)
    Team.remove_from_default_team(employee_user)
    ids_added= team.add_member_by_user_ids(ids)
    return Response(data={},status=status.HTTP_200_OK)


@transaction.atomic
@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
def remove_team_member(request):
    team_name=request.data['team']
    ids = request.data.getlist('ids')
    team = get_object_or_404(Team,name=team_name)
    ids_deleted= team.remove_member_by_user_ids(ids)
    return Response(data={'ids_deleted':ids_deleted},status=status.HTTP_200_OK)

@transaction.atomic
@api_view(['POST','DELETE','GET'])
@authentication_classes((TokenAuthentication,))
def manipulate_employee(request,object_id):
    user = get_object_or_404(User,id=object_id)
    employee = user.employee
    if(request.method=="POST"):
        email = request.data.get('email')
        password=request.data.get('password')
        telephone = request.data.get('telephone')
        name = request.data.get('name')
        if (email):
            user.username = user.email = email
        if (password):
            user.set_password(password)
        if (telephone):
            user.employee.telephone = telephone
        if (name):
            user.employee.name = name
        user.save()
        user.employee.save()
        employee.__dict__.update(request.data)
        employee.save()

        # Team.remove_from_default_team(user)
        # team = get_object_or_404(Team,name=team_name)
        # team.add_member(user)

        return_data = EmployeeProfileSerializer(employee).data
        return Response(data=return_data,status=status.HTTP_200_OK)
    elif (request.method=="DELETE"):
        user.delete()
        return Response(data={},status=status.HTTP_204_NO_CONTENT)
    elif (request.method == "GET"):
        return_data = EmployeeProfileSerializer(employee).data
        return Response(data=return_data,status=status.HTTP_200_OK)