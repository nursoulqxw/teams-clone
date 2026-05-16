# Django modules
from django.urls import reverse

# Django REST Framework
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

# Project modules
from apps.users.models import CustomUser
from apps.teams.models import Team, TeamMembership
from apps.channels.models import Channel
from apps.messages.models import Message


class MessageTestBase(APITestCase):
    """Shared fixtures for all message tests."""

    def setUp(self) -> None:
        self.client = APIClient()

        self.author: CustomUser = CustomUser.objects.create_user(
            email="author@test.com",
            password="pass",
            first_name="Author",
            last_name="User",
        )
        self.member: CustomUser = CustomUser.objects.create_user(
            email="member@test.com",
            password="pass",
            first_name="Member",
            last_name="User",
        )
        self.outsider: CustomUser = CustomUser.objects.create_user(
            email="outsider@test.com",
            password="pass",
            first_name="Out",
            last_name="Sider",
        )

        self.team: Team = Team.objects.create(
            name="Test Team",
            owner=self.author,
        )

        TeamMembership.objects.create(team=self.team, user=self.author, role="admin")
        TeamMembership.objects.create(team=self.team, user=self.member, role="member")

        self.channel: Channel = Channel.objects.create(
            name="general",
            team=self.team,
            is_private=False,
        )

        self.message: Message = Message.objects.create(
            content="Hello world",
            author=self.author,
            channel=self.channel,
        )

    def list_url(self) -> str:
        return reverse("messages-list")

    def detail_url(self, pk: int) -> str:
        return reverse("messages-detail", kwargs={"pk": pk})


# ── GET /api/messages/ ────────────────────────────────────────────────────────

class MessageListTests(MessageTestBase):

    def test_list_filtered_by_channel_id(self) -> None:
        """Team member gets only messages for the requested channel."""
        other_channel = Channel.objects.create(name="other", team=self.team)
        Message.objects.create(content="Other", author=self.author, channel=other_channel)

        self.client.force_authenticate(self.author)
        response = self.client.get(self.list_url(), {"channel_id": self.channel.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [m["id"] for m in response.data["data"]]
        self.assertIn(self.message.id, ids)
        for m in response.data["data"]:
            self.assertEqual(m["channel"]["id"], self.channel.id)

    def test_list_without_channel_filter(self) -> None:
        """Team member sees all messages across their channels."""
        self.client.force_authenticate(self.author)
        response = self.client.get(self.list_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 1)

    def test_list_outsider_sees_no_messages(self) -> None:
        """User not in team gets an empty result (queryset scoped to team)."""
        self.client.force_authenticate(self.outsider)
        response = self.client.get(self.list_url(), {"channel_id": self.channel.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)


# ── POST /api/messages/ ───────────────────────────────────────────────────────

class MessageCreateTests(MessageTestBase):

    def test_create_message_success(self) -> None:
        """Team member can create a message in their channel."""
        self.client.force_authenticate(self.author)
        response = self.client.post(self.list_url(), {
            "content": "New message",
            "channel": self.channel.id,
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["content"], "New message")

    def test_create_thread_reply(self) -> None:
        """Team member can reply to an existing message (thread)."""
        self.client.force_authenticate(self.member)
        response = self.client.post(self.list_url(), {
            "content": "Reply to parent",
            "channel": self.channel.id,
            "parent_message": self.message.id,
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["parent_message"], self.message.id)

    def test_create_message_outsider_no_access(self) -> None:
        """User not in team cannot post to a channel."""
        self.client.force_authenticate(self.outsider)
        response = self.client.post(self.list_url(), {
            "content": "Sneaky message",
            "channel": self.channel.id,
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ── GET /api/messages/{id}/ ───────────────────────────────────────────────────

class MessageRetrieveTests(MessageTestBase):

    def test_retrieve_message_success(self) -> None:
        """Team member can retrieve a message in their channel."""
        self.client.force_authenticate(self.author)
        response = self.client.get(self.detail_url(self.message.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["id"], self.message.id)

    def test_retrieve_message_not_found(self) -> None:
        """Retrieving a non-existent message returns 404."""
        self.client.force_authenticate(self.author)
        response = self.client.get(self.detail_url(99999))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_message_outsider_no_access(self) -> None:
        """User not in team cannot retrieve a message from that channel."""
        self.client.force_authenticate(self.outsider)
        response = self.client.get(self.detail_url(self.message.id))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ── PATCH /api/messages/{id}/ ─────────────────────────────────────────────────

class MessageUpdateTests(MessageTestBase):

    def test_update_by_author_success(self) -> None:
        """Author can update their own message content."""
        self.client.force_authenticate(self.author)
        response = self.client.patch(self.detail_url(self.message.id), {
            "content": "Updated content",
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["content"], "Updated content")

    def test_update_by_non_author_forbidden(self) -> None:
        """Team member who is not the author cannot edit the message."""
        self.client.force_authenticate(self.member)
        response = self.client.patch(self.detail_url(self.message.id), {
            "content": "Hijacked content",
        })

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.message.refresh_from_db()
        self.assertEqual(self.message.content, "Hello world")

    def test_update_message_not_found(self) -> None:
        """Updating a non-existent message returns 404."""
        self.client.force_authenticate(self.author)
        response = self.client.patch(self.detail_url(99999), {"content": "x"})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ── DELETE /api/messages/{id}/ ────────────────────────────────────────────────

class MessageDeleteTests(MessageTestBase):

    def test_delete_by_author_success(self) -> None:
        """Author can delete their own message."""
        self.client.force_authenticate(self.author)
        response = self.client.delete(self.detail_url(self.message.id))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Message.objects.filter(pk=self.message.id).exists())

    def test_delete_by_non_author_forbidden(self) -> None:
        """Team member who is not the author cannot delete the message."""
        self.client.force_authenticate(self.member)
        response = self.client.delete(self.detail_url(self.message.id))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Message.objects.filter(pk=self.message.id).exists())

    def test_delete_message_not_found(self) -> None:
        """Deleting a non-existent message returns 404."""
        self.client.force_authenticate(self.author)
        response = self.client.delete(self.detail_url(99999))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
