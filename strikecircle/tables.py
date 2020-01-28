import django_tables2 as tables
from strikecircle.models import Pledge


class PledgeTable(tables.Table):
    class Meta:
        model = Pledge
        template_name = "django_tables2/bootstrap.html"
        fields = ("first_name", "last_name", "email", "phone", "zipcode", "one_on_one")