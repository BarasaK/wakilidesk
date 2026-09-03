from django.core.management.base import BaseCommand

from diary.services import send_due_diary_reminders


class Command(BaseCommand):
    help = "Send due court diary reminders through configured channels."

    def handle(self, *args, **options):
        result = send_due_diary_reminders()
        self.stdout.write(
            self.style.SUCCESS(
                f"Diary reminders processed. Sent: {result['sent']}. Failed: {result['failed']}."
            )
        )
