from django.core.management.base import BaseCommand
from apps.users.models import CustomUser

class Command(BaseCommand):
    help = "Seed the database with initial users"

    def handle(self, *args, **options):
        for i in range (20,30):
            email = f"user{i}@gmail.com"
            if CustomUser.objects.filter(email=email).exists():
                continue
            CustomUser.objects.create_user(
                email=email,
                password="password123",
                first_name=f"User{i}",
                last_name="Example",
            )
        self.stdout.write(self.style.SUCCESS("Successfully seeded users"))