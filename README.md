businesslen

# Overview
This Python package calculates the business days\*/hours between two datetimes.
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

bl = BusinessLen(start_dt, end_dt)
bl.days  # 2.58
bl.hours # 20.62
```

# Documentation
```
class BusinessLen(start_dt, end_dt, workweek_schedule, lunch_hour, offdays)

    Keyword arguments:
    start_dt -- a datetime object
    end_dt -- a datetime object
    workweek_schedule -- (default: 9 to 5, Monday to Friay)
        a dict that defines weekly work hours; has following format
        {
            0: (9, 17),
            ...
            6: ()
        }
        The key is an int following datetime weekday() function where
        Monday is 0 and Sunday is 6. The value is a tuple with two ints:
        the start hour and the end hour in 24 hour format (0 to 23).
    lunch_hour -- int (default 12 PM)
    offdays -- either an ISO country code or tuple of datetime dates to be
               considered as holidays (default US holidays)
```

Off-hours are not not added. For example, if `end_dt` is 30 minutes past work
hours, those 30 minutes will be ignored.

Input verification is done upon object initialization. `ValueError` is raised
with corresponding error message if something is wrong.
