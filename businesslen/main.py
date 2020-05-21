from datetime import datetime, timedelta

import holidays


_DEFAULT_WORKWEEK_SCHEDULE = {
    0: (9, 17),
    1: (9, 17),
    2: (9, 17),
    3: (9, 17),
    4: (9, 17),
    5: (),
    6: ()
    }
_ERRCODE_MESSAGE = {
    0: "No error",
    1: "Invalid start_dt or end_dt",
    2: "Invalid workweek_schedule",
    3: "Invalid offdays",
    4: "Invalid lunch_hour"
    }


class BusinessLen:

    def __init__(self, workweek_schedule=_DEFAULT_WORKWEEK_SCHEDULE,
                 lunch_hour=12, offdays="US"):
        """Keyword arguments:
        workweek_schedule --
            a dict that defines weekly work hours; has following format
            {
                0: (9, 17),
                ...
                6: ()
            }
            The key is an int following datetime weekday() function where
            Monday is 0 and Sunday is 6. The value is a tuple with two ints:
            the start hour and the end hour in 24 hour format (0 to 23).
        lunch_hour -- int
        offdays -- either an ISO country code or tuple of datetime dates to be
                   considered as holidays
        """
        _ok, _errcode = _verify_init(workweek_schedule, lunch_hour, offdays)
        if not _ok:
            raise ValueError(_ERRCODE_MESSAGE[_errcode])
        if isinstance(offdays, str):
            self._offdays = holidays.CountryHoliday(offdays)
        else:
            self._offdays = offdays
        self._workweek_schedule = workweek_schedule
        self._lunch_hour = lunch_hour
        self._workhour_lookup = _build_workhour_lookup(workweek_schedule,
                                                       lunch_hour)

    def hours(self, start_dt, end_dt):
        """Calculate for another period."""
        _ok = _verify_dt(start_dt, end_dt)
        if not _ok:
            raise ValueError(_ERRCODE_MESSAGE[1])
        self.h = _calculate_work_hours(
            start_dt, end_dt, self._workweek_schedule, self._lunch_hour,
            self._workhour_lookup, self._offdays
            )
        return self.h

    def days(self):
        return self.h / 8


def _verify_init(workweek_schedule, lunch_hour, offdays):
    # workweek_schedule
    is_valid_workweek_schedule = _verify_workweek_schedule(workweek_schedule)
    if not is_valid_workweek_schedule:
        return (False, 2)
    # lunch_hour
    if not (isinstance(lunch_hour, int) and 0 <= lunch_hour <= 23):
        return (False, 4)
    # offdays
    if isinstance(offdays, str):
        try:
            holidays.CountryHoliday(offdays)
        except KeyError:  # package behavior
            return (False, 3)
    elif isinstance(offdays, tuple):
        for d in offdays:
            if not (isinstance(d, datetime)
                    and datetime(d.year, d.month, d.day) == d):
                return (False, 3)
    else:
        return (False, 3)
    return (True, 0)


def _verify_dt(start_dt, end_dt):
    return isinstance(start_dt, datetime) and isinstance(end_dt, datetime) \
        and end_dt >= start_dt


def _verify_workweek_schedule(schedule):
    if schedule == _DEFAULT_WORKWEEK_SCHEDULE:
        return True
    if not isinstance(schedule, dict) or len(schedule) != 7:  # num week days
        return False
    for day_of_week, work_hours, default_day_of_week in zip(
            schedule.keys(), schedule.values(), _DEFAULT_WORKWEEK_SCHEDULE):
        if day_of_week != default_day_of_week:
            return False
        if not isinstance(work_hours, tuple) or not len(work_hours) in (0, 2):
            return False
        if work_hours == ():  # off day
            continue
        start_hour, end_hour = work_hours[0], work_hours[1]
        valid_work_hours = (
            isinstance(start_hour, int) and isinstance(end_hour, int)
            and 0 <= start_hour <= 23 and 0 <= end_hour <= 23 and
            start_hour < end_hour
            )
        if not valid_work_hours:
            return False
    return True


def _build_workhour_lookup(schedule, lunch_hour):
    """Build a lookup dict to determine whether a given hour of a given day of
    week is a work hour.
    """
    res = {d: [False] * 24 for d in range(7)}
    for dow in res:
        if len(schedule[dow]) == 0:  # off day
            continue
        start_h, end_h = schedule[dow][0], schedule[dow][1]
        for wh in range(start_h, end_h):
            res[dow][wh] = True
        res[dow][lunch_hour] = False
    return res


def _calculate_work_hours(sh, eh, ww_schedule, lunch_hour, wh_lookup, offdays):
    """Calculate the total work hours in a period.
    - If sh and eh are within the same hour, subtract, done
    - Round up sh and round down eh
    - If sh and eh belong to the same day, increase sh until sh equals eh, done
    - Else, increase sh until end of day, decrease eh until start of day
    - Loop over days in between
    """
    total_hours = 0
    sh_date = _round_down_date(sh)
    eh_date = _round_down_date(eh)
    # if eh and sh within an hour
    if sh_date == eh_date and sh.hour == eh.hour \
            and _is_workhour(sh, wh_lookup, offdays):
        return (eh - sh).seconds/3600

    # round down eh before loop
    if _is_workhour(eh, wh_lookup, offdays):
        total_hours += eh.minute/60 + eh.second/3600
    eh = _round_down_hour(eh)
    # round up sh before loop
    sh_next_hour = _round_down_hour(sh) + timedelta(hours=1)
    if _is_workhour(sh, wh_lookup, offdays):
        total_hours += (sh_next_hour - sh).seconds/3600
    sh = sh_next_hour
    # if eh and sh belong to the same day
    if sh_date == eh_date:
        while sh < eh:
            if _is_workhour(sh, wh_lookup, offdays):
                total_hours += 1
            sh += timedelta(hours=1)
        return total_hours
    # else
    ## sh to end of day, eh to start of day
    sh_upper = sh_date+ timedelta(days=1)
    while sh < sh_upper:
        if _is_workhour(sh, wh_lookup, offdays):
            total_hours += 1
        sh += timedelta(hours=1)
    while eh > eh_date:
        eh -= timedelta(hours=1)
        if _is_workhour(eh, wh_lookup, offdays):
            total_hours += 1
    ## loop over days
    start_date = sh_date + timedelta(days=1)
    while start_date < eh_date:
        weekday = start_date.weekday()
        if ww_schedule[weekday] and start_date not in offdays:
            start_hour = ww_schedule[weekday][0]
            end_hour = ww_schedule[weekday][1]
            total_hours += end_hour - start_hour
            if start_hour <= lunch_hour < end_hour:
                total_hours -= 1
        start_date += timedelta(days=1)
    return total_hours


def _is_workhour(dt, wh_lookup, offdays):
    return not _round_down_date(dt) in offdays \
        and wh_lookup[dt.weekday()][dt.hour]


def _round_down_hour(dt):
    return dt - timedelta(minutes=dt.minute, seconds=dt.second)


def _round_down_date(dt):
    return datetime(dt.year, dt.month, dt.day)
