#REST modules
from rest_framework.serializers import (
    ModelSerializer,
    SerializerMethodField,
    EmailField
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
        team = obj.team_id
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
            'team_id',
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
    
    assigment = ShortAssigmentsSerializers(read_only=True)
    student_info = SerializerMethodField()

    class Meta:
        model = Assignment_Submissions
        fields = [
            'assigment',
            'student_info',
            'status',
            'submitted',
            'submitted_at'
        ]

    def get_student_info(
        self,
        obj:Assignment_Submissions
    )->dict:
        """
        Student Info
        """
        student = obj.student_id
        return {
            'id':student.id,
            'email':student.email
        }   
    

class CompletedAssigmentsSerializers(ModelSerializer):


    class Meta:
        model = Assignment_Submissions
        fields = [
            'submitted',
            'submitted_at',
            'status',
            'file'
        ]
        read_only_fields = ['submitted_at', 'status']

    def update(self, instance, validated_data):
        """
        Update submission status and submitted_at
        """
        now = timezone.now()
        due_date = instance.assigment.due_data

        new_submitted = validated_data.get('submitted', instance.submitted)

        file = validated_data.get('file')

        if file:
            instance.file = file

        if new_submitted and not instance.submitted:
        
            instance.submitted = True
            instance.submitted_at = now

            if now.date() > due_date:
                instance.status = 'completed_late'
            else:
                instance.status = 'completed'

        elif not instance.submitted and now.date() > due_date:
            instance.status = 'overdue'

        instance.save()
        return instance


class SubmissionListSerializer(ModelSerializer):

    student_email = EmailField(source='student.email')

    class Meta:
        model = Assignment_Submissions
        fields = [
            'id',
            'student_email',
            'submitted',
            'submitted_at',
            'status',
        ]


class GradeSubmissionSerializer(ModelSerializer):

    class Meta:
        model = Assignment_Submissions
        fields = ['points_awarded']


