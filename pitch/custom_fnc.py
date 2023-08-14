from datetime import date
from pitch.models import Pitch


def convert_timedelta(duration):
    days, seconds = (
        duration.days,
        duration.seconds,
    )
    hours = round(days * 24 + seconds / 3600, 2)
    return hours


def query_statistic():
    last_month = date.today().month - 1
    year = date.today().year
    pitches = Pitch.objects.raw(
        """
        SELECT p.id, p.title,sum(o.cost) as revenues, count(o.id) as count FROM orders as o
        join pitches as p on p.id = o.pitch_id
        where month(o.time_start) = %d and year(o.time_start) = %d
        group by o.pitch_id
        order by revenues desc, count desc;  
        """
        % (last_month, year)
    )
    return pitches
