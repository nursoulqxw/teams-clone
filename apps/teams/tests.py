"""
Tests for apps/teams — TeamViewSet
Covers every endpoint with success, permission, and edge-case scenarios.

Endpoints tested:
  GET    /api/teams/                    (3 tests)
  POST   /api/teams/                    (3 tests)
  GET    /api/teams/{id}/               (3 tests)
  PATCH  /api/teams/{id}/               (3 tests)
  DELETE /api/teams/{id}/               (3 tests)
  POST   /api/teams/{id}/members/       (3 tests)
  DELETE /api/teams/{id}/members/       (3 tests)
"""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from apps.users.models import CustomUser
from apps.teams.models import Team, TeamMembership
from apps.channels.models import Channel


class TeamTestBase(APITestCase):
    """
    Creates three users and two teams used across all test classes.

    owner  → owns team_a, is admin member of team_a
    member → regular member of team_a
    other  → owns team_b; completely outside team_a
    """

    def setUp(self):
        self.client = APIClient()

        # Users
        self.owner = CustomUser.objects.create_user(
            email="owner@test.com",
            password="pass1234",
            first_name="Owner",
            last_name="User",
        )
        self.member = CustomUser.objects.create_user(
            email="member@test.com",
            password="pass1234",
            first_name="Member",
            last_name="User",
        )
        self.other = CustomUser.objects.create_user(
            email="other@test.com",
            password="pass1234",
            first_name="Other",
            last_name="User",
        )

        # Teams
        self.team_a = Team.objects.create(
            name="Team Alpha",
            description="First team",
            owner=self.owner,
        )
        self.team_b = Team.objects.create(
            name="Team Beta",
            description="Second team",
            owner=self.other,
        )

        # Memberships
        TeamMembership.objects.create(team=self.team_a, user=self.owner, role="admin")
        TeamMembership.objects.create(team=self.team_a, user=self.member, role="member")
        TeamMembership.objects.create(team=self.team_b, user=self.other, role="admin")

    def list_url(self):
        return reverse("team-list")

    def detail_url(self, pk):
        return reverse("team-detail", kwargs={"pk": pk})

    def members_url(self, pk):
        return reverse("team-members", kwargs={"pk": pk})


class TeamListTests(TeamTestBase):

    def test_list_returns_all_teams_for_authenticated_user(self):
        """Any authenticated user can see all teams."""
        self.client.force_authenticate(self.owner)
        response = self.client.get(self.list_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 2)

    def test_list_filter_by_name(self):
        """?name= filters teams by name (case-insensitive contains)."""
        self.client.force_authenticate(self.member)
        response = self.client.get(self.list_url(), {"name": "alpha"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [t["name"] for t in response.data["data"]]
        self.assertIn("Team Alpha", names)
        self.assertNotIn("Team Beta", names)

    def test_list_requires_authentication(self):
        """Unauthenticated request gets 401."""
        response = self.client.get(self.list_url())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TeamCreateTests(TeamTestBase):

    def test_create_team_success(self):
        """Authenticated user can create a team; they become owner."""
        self.client.force_authenticate(self.member)
        payload = {"name": "New Team", "description": "Created by member"}
        response = self.client.post(self.list_url(), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["name"], "New Team")
        # Team must exist in DB
        self.assertTrue(Team.objects.filter(name="New Team", owner=self.member).exists())

    def test_create_team_duplicate_name_fails(self):
        """Creating a team with an existing name returns 400."""
        self.client.force_authenticate(self.owner)
        payload = {"name": "Team Alpha"}  # already exists
        response = self.client.post(self.list_url(), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_team_unauthenticated_fails(self):
        """Unauthenticated request cannot create a team."""
        payload = {"name": "Ghost Team"}
        response = self.client.post(self.list_url(), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TeamRetrieveTests(TeamTestBase):

    def test_retrieve_team_success(self):
        """Any authenticated user can retrieve a team by ID."""
        self.client.force_authenticate(self.member)
        response = self.client.get(self.detail_url(self.team_a.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["name"], "Team Alpha")

    def test_retrieve_nonexistent_team_returns_404(self):
        """Retrieving a team that does not exist returns 404."""
        self.client.force_authenticate(self.owner)
        response = self.client.get(self.detail_url(99999))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_team_unauthenticated_fails(self):
        """Unauthenticated request cannot retrieve a team."""
        response = self.client.get(self.detail_url(self.team_a.id))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TeamUpdateTests(TeamTestBase):

    def test_owner_can_update_team(self):
        """Team owner can patch name and description."""
        self.client.force_authenticate(self.owner)
        payload = {"name": "Team Alpha Updated", "description": "New description"}
        response = self.client.patch(self.detail_url(self.team_a.id), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.team_a.refresh_from_db()
        self.assertEqual(self.team_a.name, "Team Alpha Updated")

    def test_non_owner_cannot_update_team(self):
        """Regular member cannot patch the team — permission denied."""
        self.client.force_authenticate(self.member)
        payload = {"name": "Hacked Name"}
        response = self.client.patch(self.detail_url(self.team_a.id), payload, format="json")

        # Expect 403 Forbidden (or 404 if object-level permission hides the resource)
        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
        )
        self.team_a.refresh_from_db()
        self.assertNotEqual(self.team_a.name, "Hacked Name")

    def test_update_nonexistent_team_returns_404(self):
        """Patching a team that does not exist returns 404."""
        self.client.force_authenticate(self.owner)
        response = self.client.patch(self.detail_url(99999), {"name": "x"})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TeamDeleteTests(TeamTestBase):

    def test_owner_can_delete_team(self):
        """Team owner can delete their team."""
        self.client.force_authenticate(self.owner)
        team_id = self.team_a.id
        response = self.client.delete(self.detail_url(team_id))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Team.objects.filter(pk=team_id).exists())

    def test_non_owner_cannot_delete_team(self):
        """Member (non-owner) cannot delete the team."""
        self.client.force_authenticate(self.member)
        response = self.client.delete(self.detail_url(self.team_a.id))

        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
        )
        self.assertTrue(Team.objects.filter(pk=self.team_a.id).exists())

    def test_cascade_delete_removes_channels(self):
        """Deleting a team also deletes its channels (CASCADE)."""
        channel = Channel.objects.create(
            name="general",
            team=self.team_a,
            is_private=False,
        )
        channel_id = channel.id

        self.client.force_authenticate(self.owner)
        self.client.delete(self.detail_url(self.team_a.id))

        self.assertFalse(Channel.objects.filter(pk=channel_id).exists())


class TeamAddMemberTests(TeamTestBase):

    def test_owner_can_add_member(self):
        """Team owner can add a new user to the team."""
        self.client.force_authenticate(self.owner)
        payload = {"user": self.other.id, "role": "member"}
        response = self.client.post(self.members_url(self.team_a.id), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            TeamMembership.objects.filter(team=self.team_a, user=self.other).exists()
        )

    def test_cannot_add_existing_member(self):
        """Adding a user who is already a member returns 400."""
        self.client.force_authenticate(self.owner)
        payload = {"user": self.member.id, "role": "member"}
        response = self.client.post(self.members_url(self.team_a.id), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_owner_cannot_add_member(self):
        """Regular member cannot add new members."""
        self.client.force_authenticate(self.member)
        payload = {"user": self.other.id, "role": "member"}
        response = self.client.post(self.members_url(self.team_a.id), payload, format="json")

        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
        )
        self.assertFalse(
            TeamMembership.objects.filter(team=self.team_a, user=self.other).exists()
        )


class TeamRemoveMemberTests(TeamTestBase):

    def test_owner_can_remove_member(self):
        """Team owner can remove a member from the team."""
        self.client.force_authenticate(self.owner)
        payload = {"user_id": self.member.id}
        response = self.client.delete(
            self.members_url(self.team_a.id), payload, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            TeamMembership.objects.filter(team=self.team_a, user=self.member).exists()
        )

    def test_remove_nonexistent_member_returns_404(self):
        """Removing a user who is not a member returns 404."""
        self.client.force_authenticate(self.owner)
        payload = {"user_id": self.other.id}  # other is not in team_a
        response = self.client.delete(
            self.members_url(self.team_a.id), payload, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_non_owner_cannot_remove_member(self):
        """Regular member cannot remove other members."""
        self.client.force_authenticate(self.member)
        payload = {"user_id": self.owner.id}
        response = self.client.delete(
            self.members_url(self.team_a.id), payload, format="json"
        )

        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
        )
        # Owner must still be in the team
        self.assertTrue(
            TeamMembership.objects.filter(team=self.team_a, user=self.owner).exists()
        )