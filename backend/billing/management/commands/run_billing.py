from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from billing import services as billing_services


class Command(BaseCommand):
    help = 'Executes the recurring billing run for active subscriptions up to the specified date.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Run date in YYYY-MM-DD format (defaults to today)'
        )

    def handle(self, *args, **options):
        date_str = options.get('date')
        if date_str:
            run_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            run_date = timezone.localdate()

        self.stdout.write(self.style.NOTICE(f"Executing ProofBill billing run as of {run_date}..."))
        result = billing_services.run(run_date=run_date)
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully completed billing run! "
                f"Invoices created: {result.invoices_created}, Total billed: Rs. {result.total_billed}"
            )
        )
