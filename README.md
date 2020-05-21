businesslen

# Overview
This Python package calculates the business hours/days\* between two datetimes.
It is possible to customize the work week schedule and list of holidays.

The default work week schedule is 9 AM to 5 PM, Monday to Friday, with a lunch
break from 12 PM to 1 PM. The default holiday schedule is US from the package
[holidays](https://pypi.org/project/holidays/).

\* Business days are eight-hour workday.

# Installation
`pip install businesslen`

# Usage
```
from datetime import datetime

from businesslen import BusinessLen


start_dt = datetime(2020, 2, 10, 8, 5, 12)
end_dt = datetime(2020, 2, 12, 16, 37, 28)

bl = BusinessLen()
bl.hours(start_dt, end_dt) # 20.62
bl.days()  # 2.58
```

# Documentation
```
def __init__(workweek_schedule, lunch_hour, offdays):
    """"Keyword arguments:
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

def hours(self, start_dt, end_dt):
    """Return business hours.

    Keyword arguments:
    start_dt -- datetime object of start time
    end_dt -- datetime object of end time
    """

def days(self):
    """Return business days."""
```

Off-hours are not not added. For example, if `end_dt` is 30 minutes past work
hours, those 30 minutes will be ignored.

Input verification is done upon object initialization and each calculation.
`ValueError` is raised with corresponding error message if something is wrong.
