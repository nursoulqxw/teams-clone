#REST modules
from rest_framework.serializers import (
    ModelSerializer,
    SerializerMethodField
)

#Django modules
from django.utils import timezone

#Project modules
from .models import (
    Assignments,
    Assignment_Submissions
)


class AssigmentsSerialzers(ModelSerializer):
    """
    Serializers Assigments
    """

    team_info = SerializerMethodField()

    class Meta:
        model = Assignments
        fields = [
            'team_info',
            'title',
            'description',
            'due_data',
            'max_points'
        ]
    
    def get_team_info(
        self,
        obj:Assignments
    )->dict:
        """
        Team Info (name,id)
        """
        team = obj.team
        return {
            'id':team.id,
            'name':team.name
        }


class ShortAssigmentsSerializers(ModelSerializer):
    """
    Short Assigments Serializers
    """
    class Meta:
        model = Assignments
        fields = [
            'id',
            'title'
        ]

class CreateAssigmentsSerializers(ModelSerializer):
    """
    Create Assigments
    """
    
    class Meta:
        model = Assignments
        fields = [
            'team',
            'title',
            'description',
            'due_data',
            'max_points'
        ]


class UpdateAssigmentsSerializers(ModelSerializer):
    """
    Update Assigments
    """
    
    class Meta:
        model = Assignments
        fields = [
            'max_points',
            'due_data'
        ]


class AssigmentsSubmissionsSerializers(ModelSerializer):
    """
    Assigmnets Submissions
    """
    assigment_id = ShortAssigmentsSerializers()
    student_info = SerializerMethodField()

    class Meta:
        model = Assignment_Submissions
        fields = [
            'assignment',
            'student_info',
            'status',
            'points_awarded'
        ]

    def get_student_info(
        self,
        obj:Assignment_Submissions
    )->dict:
        """
        Student Info
        """
        student = obj.student
        return {
            'id':student.id,
            'full_name':student.get_full_name(),
            'email':student.email
        }   
    

class CompletedAssigmentsSerializers(ModelSerializer):
    """
    Assigments status : (Overdue,Upcoming,Completed)
    """
    
    class Meta:
        model = Assignment_Submissions
        fields = [
            'status',
            'submitted_at'
        ]

    def update(
        self, 
        instance, 
        validated_data
    ):
        """
        Updata for status
        """
        now = timezone.now()
        due_data = instance.assigment.due_data

        
        if instance.submitted:
            instance.submitted_at = now

            if now.date() > due_data:
                instance.status = 'completed_late'
            else:
                instance.status = 'completed'
        
        else:
            if now.date() > due_data:
                instance.status = 'overdue'
                
        instance.save()
        return instance
    



