import datetime, calendar

def add_months(date, months):
    mon = date.month + months - 1
    yr = date.year + mon / 12
    mon = mon % 12 + 1
    day = min(date.day, calendar.monthrange(yr, mon)[1])
    return datetime.date(yr, mon, day)

