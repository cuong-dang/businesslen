from copy import deepcopy
from datetime import datetime, timedelta
import unittest

from businesslen import main


DEFAULT_DECIMAL_PRECISION = 7
TCB_WORKWEEK_SCHEDULE = {0: (8, 17), 1: (8, 17), 2: (8, 17), 3: (8, 17),
                         4: (8, 17), 5: (8, 12), 6: ()}


class TestVerifyInit(unittest.TestCase):

    def test_valid_period(self):
        # invalid type
        start_dt, end_dt = None, None
        self.assertEqual(main._verify_dt(start_dt, end_dt), False)
        # end_dt < start_dt
        start_dt = datetime.now()
        end_dt = start_dt - timedelta(days=1)
        self.assertEqual(main._verify_dt(start_dt, end_dt), False)
        # valid
        start_dt, end_dt = datetime.now(), datetime.now()
        self.assertEqual(main._verify_dt(start_dt, end_dt), True)

    def test_valid_workweek_schedule(self):
        # invalid schedule as a whole
        ## invalid type
        schedule = None
        self.assertEqual(main._verify_workweek_schedule(schedule), False)
        ## not enough week days
        schedule = {0: (), 1: (), 2: ()}
        self.assertEqual(main._verify_workweek_schedule(schedule), False)
        # invalid day of week
        ## invalid week day codes
        schedule = {0: (), 1: (), 2: (), 3: (), 4: (), 5: (), 7: (),}
        self.assertEqual(main._verify_workweek_schedule(schedule), False)
        # invalid work hours
        ## invalid type
        schedule = deepcopy(main._DEFAULT_WORKWEEK_SCHEDULE)
        schedule[0] = None
        ## invalid tuple length
        self.assertEqual(main._verify_workweek_schedule(schedule), False)
        schedule[0] = (0, 0, -1)
        ## invalid hours
        self.assertEqual(main._verify_workweek_schedule(schedule), False)
        schedule[0] = (0, 25)
        ## start_hour >= end_hour
        self.assertEqual(main._verify_workweek_schedule(schedule), False)
        schedule[0] = (0, 0)
        self.assertEqual(main._verify_workweek_schedule(schedule), False)
        # valid
        schedule = TCB_WORKWEEK_SCHEDULE
        self.assertEqual(main._verify_workweek_schedule(schedule), True)

        # lunch_hour
        self.assertEqual(
            main._verify_init(TCB_WORKWEEK_SCHEDULE, None, ()), (False, 4)
            )
        self.assertEqual(
            main._verify_init(TCB_WORKWEEK_SCHEDULE, 13, ()), (True, 0)
            )

    def test_valid_offdays(self):
        # invalid type
        self.assertEqual(
            main._verify_init(main._DEFAULT_WORKWEEK_SCHEDULE, 12, None),
            (False, 3)
            )
        # invalid country code
        self.assertEqual(
            main._verify_init(main._DEFAULT_WORKWEEK_SCHEDULE, 12, "0"),
            (False, 3)
            )
        # invalid datetime list
        self.assertEqual(
            main._verify_init(main._DEFAULT_WORKWEEK_SCHEDULE, 12, [0]),
            (False, 3)
            )
        # "non-rounded" datetime list
        self.assertEqual(
            main._verify_init(main._DEFAULT_WORKWEEK_SCHEDULE, 12,
                              (datetime(2020, 1, 1, 12, 0, 0))),
            (False, 3)
            )
        # valid country code
        self.assertEqual(
            main._verify_init(main._DEFAULT_WORKWEEK_SCHEDULE, 12, "US"),
            (True, 0)
            )
        # valid datetime list
        self.assertEqual(
            main._verify_init(main._DEFAULT_WORKWEEK_SCHEDULE, 12,
                              (datetime(2020, 1, 1),)),
            (True, 0)
            )


class TestCore(unittest.TestCase):

    def test_build_workhour_lookup(self):
        # DEFAULT WORKWEEK SCHEDULE
        schedule = main._DEFAULT_WORKWEEK_SCHEDULE
        workhour_lookup = {d: [False] * 24 for d in range(7)}
        nine_to_five = [False] * 9 + [True] * 8 + [False] * 7
        nine_to_five[12] = False  # lunch break
        for dow in range(0, 5):
            workhour_lookup[dow] = nine_to_five
        self.assertEqual(main._build_workhour_lookup(schedule, 12),
                         workhour_lookup)
        # TCB WORKWEEK SCHEDULE
        schedule = TCB_WORKWEEK_SCHEDULE
        workhour_lookup = {d: [False] * 24 for d in range(7)}
        eight_to_five = [False] * 8 + [True] * 9 + [False] * 7
        eight_to_five[12] = False  # lunch break
        for dow in range(0, 5):
            workhour_lookup[dow] = eight_to_five
        workhour_lookup[5][8:12] = [True] * 4
        self.assertEqual(main._build_workhour_lookup(schedule, 12),
                         workhour_lookup)

    def test_is_workhour(self):
        offdays = (datetime(2020, 1, 1), )
        wh_lookup = main._build_workhour_lookup(TCB_WORKWEEK_SCHEDULE, 12)
        self.assertTrue(main._is_workhour(datetime(2020, 1, 2, 14, 30, 30),
                                          wh_lookup, offdays))
        self.assertFalse(main._is_workhour(datetime(2020, 1, 1, 14, 30, 30),
                                           wh_lookup, offdays))
        self.assertFalse(main._is_workhour(datetime(2020, 1, 2, 12, 30, 30),
                                           wh_lookup, offdays))

    def test_round_down_hour(self):
        self.assertEqual(
            main._round_down_hour(datetime(2020, 1, 15, 17, 30, 30)),
            datetime(2020, 1, 15, 17, 0, 0)
            )

    def test_calculate_work_hours(self):
        offdays = (datetime(2020, 1, 1), )
        bl = main.BusinessLen(TCB_WORKWEEK_SCHEDULE, 12, offdays)
        # same day, same hour
        sh = datetime(2020, 1, 2, 8, 0, 0)
        eh = datetime(2020, 1, 2, 8, 30, 0)
        self.assertEqual(bl.hours(sh, eh), 0.5)
        # same day, different hours
        sh = datetime(2020, 1, 2, 8, 0, 0)
        eh = datetime(2020, 1, 2, 9, 0, 0)
        self.assertEqual(bl.hours(sh, eh), 1)
        sh = datetime(2020, 1, 2, 8, 0, 0)
        eh = datetime(2020, 1, 2, 11, 30, 0)
        self.assertEqual(bl.hours(sh, eh), 3.5)
        # same day, different hours, cross lunch
        sh = datetime(2020, 1, 2, 8, 0, 0)
        eh = datetime(2020, 1, 2, 12, 30, 0)
        self.assertEqual(bl.hours(sh, eh), 4)
        sh = datetime(2020, 1, 2, 8, 0, 0)
        eh = datetime(2020, 1, 2, 14, 30, 0)
        self.assertEqual(bl.hours(sh, eh), 5.5)
        sh = datetime(2020, 1, 2, 12, 0, 0)
        eh = datetime(2020, 1, 2, 13, 30, 0)
        self.assertEqual(bl.hours(sh, eh), 0.5)
        # same day, different hours, not in workhour
        sh = datetime(2020, 1, 2, 8, 0, 0)
        eh = datetime(2020, 1, 2, 18, 30, 0)
        self.assertEqual(bl.hours(sh, eh), 8)
        sh = datetime(2020, 1, 2, 7, 0, 0)
        eh = datetime(2020, 1, 2, 12, 30, 0)
        self.assertEqual(bl.hours(sh, eh), 4)
        sh = datetime(2020, 1, 2, 7, 0, 0)
        eh = datetime(2020, 1, 2, 8, 0, 0)
        self.assertEqual(bl.hours(sh, eh), 0)
        # different days
        sh = datetime(2020, 1, 2, 7, 0, 0)
        eh = datetime(2020, 1, 3, 8, 0, 0)
        self.assertEqual(bl.hours(sh, eh), 8)
        sh = datetime(2020, 1, 2, 7, 0, 0)
        eh = datetime(2020, 1, 3, 16, 0, 0)
        self.assertEqual(bl.hours(sh, eh), 15)
        sh = datetime(2020, 1, 2, 10, 0, 0)
        eh = datetime(2020, 1, 7, 16, 0, 0)
        self.assertEqual(bl.hours(sh, eh), 33)
        # different days, cross holiday
        sh = datetime(2019, 12, 31, 7, 0, 0)
        eh = datetime(2020, 1, 3, 8, 0, 0)
        self.assertEqual(bl.hours(sh, eh), 16)
        sh = datetime(2020, 1, 1, 7, 0, 0)
        eh = datetime(2020, 1, 2, 16, 0, 0)
        self.assertEqual(bl.hours(sh, eh), 7)
        # some "not-so-round" hours
        sh = datetime(2020, 1, 2, 8, 5, 12)
        eh = datetime(2020, 1, 2, 16, 37, 28)
        self.assertEqual(round(bl.hours(sh, eh), DEFAULT_DECIMAL_PRECISION),
                         round(27136/3600, DEFAULT_DECIMAL_PRECISION))
        # some edge cases
        sh = datetime(2020, 1, 2, 8, 5, 12)
        eh = datetime(2020, 1, 2, 8, 5, 12)
        self.assertEqual(bl.hours(sh, eh), 0)


if __name__ == "__main__":
    unittest.main()
