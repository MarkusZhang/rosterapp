from django.db import models
from django.contrib.auth.models import User

from common.abcmodels import TimeStampedModel

class NotificationItem(TimeStampedModel):
    ROSTER_RESULT_OUT=0
    ROSTER_CHANGED=1
    TIMETABLE_POLLING_OPEN=2
    DUTY_ASSIGNED=3
    SWAP_SLOT_REQUEST=4
    SWAP_SLOT_APPROVED=5
    SWAP_SLOT_REJECTED=6
    REQUESTED_TO_JOIN_TEAM=7
    ADD_MEMBER_REQUEST_APPROVED=8
    NOTIFICATION_TYPES=(
        (ROSTER_RESULT_OUT,'Roster result out'),# for manager
        (ROSTER_CHANGED,'Roster arrangement changed'), # for manager
        (TIMETABLE_POLLING_OPEN,'Time table polling'),
        (DUTY_ASSIGNED,'New duty assigned'),
        (SWAP_SLOT_REQUEST,'New request for swapping time slot is received'),
        (SWAP_SLOT_APPROVED,'You request to swap is approved'),
        (SWAP_SLOT_REJECTED,'You request to swap is rejected'),
        (REQUESTED_TO_JOIN_TEAM,"You are requested to join a team"),
        (ADD_MEMBER_REQUEST_APPROVED,"Your request to add member is approved"),
    )
    type=models.IntegerField(choices=NOTIFICATION_TYPES)
    message=models.TextField()
    detail=models.TextField() # a serialized dict object that contains details
    for_user=models.ForeignKey(User)
    is_read=models.BooleanField(default=False)

    def __unicode__(self):
        return self.message