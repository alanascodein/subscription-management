from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from audit import proof_engine


class Command(BaseCommand):
    help = 'Executes the deterministic Proof Engine audit detection across subscriptions and invoices.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--as-of',
            type=str,
            help='As-of date in YYYY-MM-DD format (defaults to today)'
        )

    def handle(self, *args, **options):
        as_of_str = options.get('as_of')
        if as_of_str:
            as_of_date = datetime.strptime(as_of_str, '%Y-%m-%d').date()
        else:
            as_of_date = timezone.localdate()

        self.stdout.write(self.style.NOTICE(f"Running Proof Engine audit as of {as_of_date}..."))
        summary = proof_engine.run(as_of=as_of_date)
        self.stdout.write(
            self.style.SUCCESS(
                f"Audit completed! "
                f"New Alerts: {summary.alerts_created}, Existing Alerts: {summary.alerts_existing}, "
                f"Revenue at Risk: Rs. {summary.revenue_at_risk}"
            )
        )
