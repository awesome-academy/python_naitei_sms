def convert_timedelta(duration):
    days, seconds = (
        duration.days,
        duration.seconds,
    )
    hours = round(days * 24 + seconds / 3600, 2)
    return hours
