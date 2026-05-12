"""
Endpoints tested:
  GET    /api/assignment/                      - list assignments
  POST   /api/assignment/                      - create assignment
  GET    /api/assignment/{id}/                 - retrieve assignment
  PATCH  /api/assignment/{id}/                 - update assignment
  POST   /api/assignment/{id}/submit/          - submit assignment
  GET    /api/assignment/{id}/submissions/     - list submissions (owner)
  POST   /api/assignment/{id}/grade/{sub_id}/  - grade a submission
"""

import datetime

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from apps.users.models import CustomUser
from apps.teams.models import Team, TeamMembership
from apps.assigments.models import Assignments, Assignment_Submissions


class AssignmentTestBase(APITestCase):
    """
    owner   → owns the team (can create / update assignments)
    student → team member (can submit assignments)
    outsider → not in the team at all
    """

    def setUp(self):
        self.client = APIClient()

        # Users
        self.owner = CustomUser.objects.create_user(
            email="owner@assign.com",
            password="pass1234",
            first_name="Owner",
            last_name="User",
        )
        self.student = CustomUser.objects.create_user(
            email="student@assign.com",
            password="pass1234",
            first_name="Student",
            last_name="User",
        )
        self.outsider = CustomUser.objects.create_user(
            email="outsider@assign.com",
            password="pass1234",
            first_name="Out",
            last_name="Sider",
        )

        # Team
        self.team = Team.objects.create(
            name="Assign Team",
            owner=self.owner,
        )
        TeamMembership.objects.create(team=self.team, user=self.owner, role="admin")
        TeamMembership.objects.create(team=self.team, user=self.student, role="member")

        # Assignment (due tomorrow → not overdue)
        self.due_future = (timezone.now() + datetime.timedelta(days=1)).date()
        self.due_past = (timezone.now() - datetime.timedelta(days=1)).date()

        self.assignment = Assignments.objects.create(
            team_id=self.team,
            title="Homework 1",
            description="Solve problems",
            due_data=self.due_future,
            max_points=100,
        )


    def list_url(self):
        return reverse("assignment-list")

    def detail_url(self, pk):
        return reverse("assignment-detail", kwargs={"pk": pk})

    def submit_url(self, pk):
        return reverse("assignment-submit", kwargs={"pk": pk})

    def submissions_url(self, pk):
        return reverse("assignment-submissions", kwargs={"pk": pk})

    def grade_url(self, pk, sub_id):
        return reverse("assignment-grade", kwargs={"pk": pk, "submission_id": sub_id})


class AssignmentListTests(AssignmentTestBase):

    def test_list_returns_assignments(self):
        """Any authenticated user can list assignments."""
        self.client.force_authenticate(self.owner)
        response = self.client.get(self.list_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["data"]), 1)

    def test_list_filter_by_team_id(self):
        """?team_id= filters assignments to a specific team."""
        other_team = Team.objects.create(name="Other Team", owner=self.outsider)
        Assignments.objects.create(
            team_id=other_team,
            title="Other HW",
            description="desc",
            due_data=self.due_future,
            max_points=50,
        )
        self.client.force_authenticate(self.owner)
        response = self.client.get(self.list_url(), {"team_id": self.team.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [a["title"] for a in response.data["data"]]
        self.assertIn("Homework 1", titles)
        self.assertNotIn("Other HW", titles)

    def test_list_requires_authentication(self):
        """Unauthenticated request is rejected."""
        response = self.client.get(self.list_url())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AssignmentCreateTests(AssignmentTestBase):

    def test_owner_can_create_assignment(self):
        """Team owner can create an assignment."""
        self.client.force_authenticate(self.owner)
        payload = {
            "team_id": self.team.id,
            "title": "Quiz 1",
            "description": "Short quiz",
            "due_data": str(self.due_future),
            "max_points": 50,
        }
        response = self.client.post(self.list_url(), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Assignments.objects.filter(title="Quiz 1").exists())

    def test_non_owner_cannot_create_assignment(self):
        """Student (non-owner) cannot create assignments — permission denied."""
        self.client.force_authenticate(self.student)
        payload = {
            "team_id": self.team.id,
            "title": "Sneaky Assignment",
            "description": "...",
            "due_data": str(self.due_future),
            "max_points": 10,
        }
        response = self.client.post(self.list_url(), payload, format="json")

        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_400_BAD_REQUEST],
        )
        self.assertFalse(Assignments.objects.filter(title="Sneaky Assignment").exists())

    def test_create_assignment_missing_fields_fails(self):
        """Creating assignment without required fields returns 400."""
        self.client.force_authenticate(self.owner)
        payload = {"team_id": self.team.id}  # missing title, due_data, max_points
        response = self.client.post(self.list_url(), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AssignmentRetrieveTests(AssignmentTestBase):

    def test_retrieve_assignment_success(self):
        """Any authenticated user can retrieve an assignment."""
        self.client.force_authenticate(self.student)
        response = self.client.get(self.detail_url(self.assignment.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["title"], "Homework 1")

    def test_retrieve_nonexistent_returns_404(self):
        """Retrieving a non-existent assignment returns 404."""
        self.client.force_authenticate(self.owner)
        response = self.client.get(self.detail_url(99999))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_requires_authentication(self):
        """Unauthenticated request is rejected."""
        response = self.client.get(self.detail_url(self.assignment.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AssignmentUpdateTests(AssignmentTestBase):

    def test_owner_can_update_assignment(self):
        """Team owner can update max_points and due_data."""
        self.client.force_authenticate(self.owner)
        new_due = str((timezone.now() + datetime.timedelta(days=7)).date())
        payload = {"max_points": 200, "due_data": new_due}
        response = self.client.patch(
            self.detail_url(self.assignment.id), payload, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assignment.refresh_from_db()
        self.assertEqual(self.assignment.max_points, 200)

    def test_student_cannot_update_assignment(self):
        """Student cannot update assignments."""
        self.client.force_authenticate(self.student)
        payload = {"max_points": 0}
        response = self.client.patch(
            self.detail_url(self.assignment.id), payload, format="json"
        )

        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_400_BAD_REQUEST],
        )

    def test_update_nonexistent_assignment_returns_404(self):
        """Updating non-existent assignment returns 404."""
        self.client.force_authenticate(self.owner)
        response = self.client.patch(self.detail_url(99999), {"max_points": 10})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AssignmentSubmitTests(AssignmentTestBase):

    def test_student_can_submit_assignment(self):
        """Team member can submit an assignment on time → status 'completed'."""
        self.client.force_authenticate(self.student)
        payload = {"submitted": True}
        response = self.client.post(
            self.submit_url(self.assignment.id), payload, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["status"], "completed")

    def test_submit_past_due_marks_completed_late(self):
        """Submitting after the due date → status 'completed_late'."""
        overdue_assignment = Assignments.objects.create(
            team_id=self.team,
            title="Overdue HW",
            description="Late",
            due_data=self.due_past,
            max_points=50,
        )
        self.client.force_authenticate(self.student)
        payload = {"submitted": True}
        response = self.client.post(
            self.submit_url(overdue_assignment.id), payload, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["status"], "completed_late")

    def test_outsider_cannot_submit(self):
        """User not in the team cannot submit."""
        self.client.force_authenticate(self.outsider)
        payload = {"submitted": True}
        response = self.client.post(
            self.submit_url(self.assignment.id), payload, format="json"
        )

        # View uses IsTeamMember permission for POST
        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED],
        )


class AssignmentSubmissionsListTests(AssignmentTestBase):

    def setUp(self):
        super().setUp()
        # Pre-create a submission for the student
        self.submission = Assignment_Submissions.objects.create(
            assigment=self.assignment,
            student_id=self.student,
            submitted=True,
            submitted_at=timezone.now(),
            status="completed",
        )

    def test_owner_can_list_submissions(self):
        """Team owner can see all submissions for an assignment."""
        self.client.force_authenticate(self.owner)
        response = self.client.get(self.submissions_url(self.assignment.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_student_cannot_list_submissions(self):
        """Regular student cannot access the submissions list."""
        self.client.force_authenticate(self.student)
        response = self.client.get(self.submissions_url(self.assignment.id))

        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
        )

    def test_submissions_for_nonexistent_assignment_returns_404(self):
        """Requesting submissions for a non-existent assignment returns 404."""
        self.client.force_authenticate(self.owner)
        response = self.client.get(self.submissions_url(99999))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AssignmentGradeTests(AssignmentTestBase):

    def setUp(self):
        super().setUp()
        self.submission = Assignment_Submissions.objects.create(
            assigment=self.assignment,
            student_id=self.student,
            submitted=True,
            submitted_at=timezone.now(),
            status="completed",
        )

    def test_owner_can_grade_submission(self):
        """Team owner can assign points to a submission."""
        self.client.force_authenticate(self.owner)
        payload = {"points_awarded": 95.0}
        response = self.client.post(
            self.grade_url(self.assignment.id, self.submission.id),
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.points_awarded, 95.0)

    def test_student_cannot_grade_submission(self):
        """Student cannot grade submissions."""
        self.client.force_authenticate(self.student)
        payload = {"points_awarded": 100.0}
        response = self.client.post(
            self.grade_url(self.assignment.id, self.submission.id),
            payload,
            format="json",
        )

        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
        )

    def test_grade_nonexistent_submission_returns_404(self):
        """Grading a submission that doesn't exist returns 404."""
        self.client.force_authenticate(self.owner)
        payload = {"points_awarded": 50.0}
        response = self.client.post(
            self.grade_url(self.assignment.id, 99999),
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)