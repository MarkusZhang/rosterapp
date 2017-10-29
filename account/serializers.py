from django.contrib.auth.models import User
from django.core.mail import send_mail

from rest_framework import serializers
from rest_framework.authtoken.models import Token

from common.serializers import IdModelSerializer
from roster.settings import EMAIL_HOST_USER
from models import Manager,VerificationToken,Employee,Team,TeamMember

class CreateUserSerializer(serializers.Serializer):
    """
    This class only serves as a base class
    """
    email=serializers.EmailField()
    password=serializers.CharField(max_length=200)
    name=serializers.CharField(max_length=200)
    telephone=serializers.CharField()

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

    def validate_email(self, value):
        # check for uniqueness of email
        if (User.objects.filter(email=value)):
            raise serializers.ValidationError("Email "+ value + " has already been used!")
        return value

    def do_email_verification(self,user):
        email_verification_token=VerificationToken()
        email_verification_token.user=user
        email_verification_token.save()
        title="Verify your email"
        content="Click on the following link: " + email_verification_token.token
        send_mail(title,content,EMAIL_HOST_USER,[user.email])


class CreateManagerSerializer(CreateUserSerializer):
    def create(self, validated_data):
        user=super(CreateManagerSerializer,self).create(validated_data)
        manager= Manager.objects.create(
            user=user,
            name=validated_data['name'],
            telephone=validated_data['telephone']
        )
        # email verification
        self.do_email_verification(user=user)
        # token for authentication
        token = Token.objects.create(user=user)
        return user,token.key



class CreateEmployeeSerializer(CreateUserSerializer):
    gender=serializers.ChoiceField(choices=[('male','male'),('female','female')],allow_null=True,required=False)
    team=serializers.CharField(allow_blank=True,allow_null=True,required=False)

    def validate_team(self, value):
        if (value and not Team.objects.filter(name=value)):
            raise serializers.ValidationError("Team "+ value + " doesn't exist!")
        return value

    def create(self, validated_data):
        user=super(CreateEmployeeSerializer,self).create(validated_data)
        gender_number= Employee.FEMALE if validated_data['gender']=='female' else Employee.MALE
        # create employee
        employee=Employee.objects.create(
            user=user,
            gender=gender_number,
            name=validated_data['name'],
            telephone=validated_data['telephone']
        )
        # create team membership if specified
        team_name=validated_data.get('team')
        if (team_name):
            # create team relationship, no need for email verification
            team=Team.objects.get(name=team_name)
            TeamMember.objects.create(
                member=Employee,
                team=team
            )
        else:
            # send email verification
            self.do_email_verification(user=user)
        # token for authentication
        token = Token.objects.create(user=user)
        return user,token.key

class TeamSerializer(serializers.ModelSerializer):
    head= serializers.CharField(source="get_head_name")

    class Meta:
        model= Team
        fields= ['id','name','head']

class TeamMemberSerializer(serializers.ModelSerializer):
    team = serializers.CharField(source='get_team_name')
    member_name = serializers.CharField(source='get_email',read_only=True)
    member_email = serializers.CharField(source='get_name',read_only=True)
    id = serializers.IntegerField(source="get_user_id")

    class Meta:
        model = TeamMember
        fields = ['id','team','member_name','member_email']

class EmployeeProfileSerializer(serializers.ModelSerializer):
    performance_grade=serializers.IntegerField(source='performance')
    id = serializers.IntegerField(source="get_user_id")
    type = serializers.CharField(source="get_type")
    email=serializers.EmailField(source="get_email")
    team_ids=serializers.ListField(source="get_team_ids")
    team_names=serializers.ListField(source="get_team_names")

    class Meta:
        model = Employee
        fields = ['name','telephone','performance_grade',
                  'on_leave','id','type','email',"team_ids","team_names"]

class ManagerProfileSerializer(IdModelSerializer):
    class Meta:
        model =Manager
