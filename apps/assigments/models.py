from django.db.models import (
    Model,
    CharField,
    ForeignKey,
    CASCADE,
    TextField,
    DateTimeField,
    IntegerField,
    FloatField,
    BooleanField,
    DateField
    
)
from apps.abstract.models import AbstractModel

from apps.team.models import Team
from apps.users.models import CustomUser


class Assignments(AbstractModel):
    team_id = ForeignKey(
        Team,
        on_delete = CASCADE,
        related_name= 'team_id'
    )
    title = CharField(
        max_length=200,
        help_text='Title'
    )
    description = TextField()
    due_data = DateField()
    max_points = IntegerField(
        help_text='Points'
    )

    def __str__(self):
        return f'Assigments - team:{self.team_id},title:{self.title}'
    
    def count_assigments(self):
        return self.title.count()
    

class Assignment_Submissions(Model):

    STATUS = [
        ('upcoming', 'Upcoming'),
        ('overdue', 'Overdue'),
        ('completed', 'Completed'),
        ('completed_late','Completed_Late')
    ]   

    assigment = ForeignKey(
        Assignments,
        on_delete=CASCADE,
        related_name='submissions'
    )
    student_id = ForeignKey(
        CustomUser,
        on_delete=CASCADE,
        related_name='student'
    )
    status = CharField(
        max_length=20,
        choices=STATUS,
        default='upcoming'
    )
    points_awarded = FloatField(
        default=0.0
    )
    submitted = BooleanField(
        default=False
    )
    submitted_at = DateTimeField(
        blank=True,
        null=True
    )

    def __str__(self):
        return f'Assigment ID:{self.assigment_id},status:{self.status}'


