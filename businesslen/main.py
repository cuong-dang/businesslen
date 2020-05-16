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
    4: "Invalid offdays"
    }


class BusinessLen:

    def __init__(self, start_dt, end_dt,
                 workweek_schedule=_DEFAULT_WORKWEEK_SCHEDULE, offdays="US"):
        """Main object

        Keyword arguments:
        start_dt -- a datetime object
        end_dt -- a datetime object
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
        offdays -- either an ISO country code or list of datetime dates to be
                   considered as holidays
        """
        self.ok, self.errcode = _verify_init(
            start_dt, end_dt, workweek_schedule, offdays
            )
        self.errmess = _ERRCODE_MESSAGE[self.errcode]
        _total_work_hours = -1
        self.days, self.hours, self.minutes, self.seconds = -1, -1, -1, -1
        if self.ok:
            if isinstance(offdays, str):
                _offdays = holidays.CountryHoliday(offdays)
            else:
                _offdays = offdays
            _workhour_lookup = _build_workhour_lookup(workweek_schedule)
            _total_work_hours = _calculate_work_hours(
                start_dt, end_dt, _workhour_lookup, _offdays
                )
            self.days = _total_work_hours / 8
            self.hours = _total_work_hours
            self.minutes = round(_total_work_hours * 60)
            self.seconds = round(_total_work_hours * 3600)


def _verify_init(start_dt, end_dt, workweek_schedule, offdays):
    # start_dt & end_dt
    is_valid_period = (
        isinstance(start_dt, datetime) and isinstance(end_dt, datetime)
        and end_dt >= start_dt
        )
    if not is_valid_period:
        return (False, 1)
    # workweek_schedule
    is_valid_workweek_schedule = _verify_workweek_schedule(workweek_schedule)
    if not is_valid_workweek_schedule:
        return (False, 2)
    # holidays country code
    if isinstance(offdays, str):
        try:
            holidays.CountryHoliday(offdays)
        except KeyError:
            return (False, 3)
    elif isinstance(offdays, list):
        for d in offdays:
            if not isinstance(d, datetime):
                return (False, 3)
    else:
        return (False, 3)
    return (True, 0)


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
            and 0 <= start_hour <= 24 and 0 <= end_hour <= 24 and
            start_hour < end_hour
            )
        if not valid_work_hours:
            return False
    return True


def _build_workhour_lookup(schedule):
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
        res[dow][12] = False  # lunch break
    return res


def _calculate_work_hours(sh, eh, wh_lookup, offdays):
    """Calculate the total work hours in a period. The algorithm is simple and
    not most efficient but the performance hit is negligible. We start by
    "trimming" the start hour and the end hour by rounding them down and up,
    respectively, and add any decimal parts if either one is a work hour. Then
    we begin the main loop that keeps increasing the start hour by one hour and
    adding it to the total work hours if the increased hour is a work hour
    until the start hour equals the end hour.
    """
    total_hours = 0
    # if eh and sh within an hour, we simply subtract
    if datetime.date(eh) == datetime.date(sh) and sh.hour == eh.hour \
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
    # main loop
    while sh < eh:
        if _is_workhour(sh, wh_lookup, offdays):
            total_hours += 1
        sh += timedelta(hours=1)
    return total_hours


def _is_workhour(dt, wh_lookup, offdays):
    return not datetime(dt.year, dt.month, dt.day, 0, 0, 0) in offdays \
        and wh_lookup[dt.weekday()][dt.hour]


def _round_down_hour(dt):
    return dt - timedelta(minutes=dt.minute, seconds=dt.second)
