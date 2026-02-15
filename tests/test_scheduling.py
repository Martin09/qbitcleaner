"""Tests for cron-based scheduling."""

from datetime import datetime

import pytest
from cron_converter import Cron


class TestCronScheduling:
    """Test cron expression parsing and next-run calculation."""

    @pytest.mark.parametrize(
        "expr",
        [
            "* * * * *",  # every minute
            "0 * * * *",  # every hour
            "0 0 * * *",  # daily at midnight
            "0 0 * * 0",  # weekly on Sunday
            "*/5 * * * *",  # every 5 minutes
            "0 */6 * * *",  # every 6 hours
            "0 3 * * *",  # daily at 3 AM
            "0 0 1 * *",  # first of every month
        ],
    )
    def test_valid_cron_expressions(self, expr):
        """Valid cron expressions should parse without error and produce a next run time."""
        cron = Cron(expr)
        schedule = cron.schedule(datetime(2026, 1, 1, 0, 0))
        next_run = schedule.next()
        assert isinstance(next_run, datetime)

    @pytest.mark.parametrize("expr", ["bad", "* * *", "60 * * * *"])
    def test_invalid_cron_expressions(self, expr):
        """Invalid cron expressions should raise an error."""
        with pytest.raises(ValueError):
            Cron(expr)

    def test_next_run_is_in_the_future(self):
        """The next scheduled run should be after the reference time."""
        cron = Cron("0 0 * * *")  # daily at midnight
        ref = datetime(2026, 6, 15, 10, 30)
        schedule = cron.schedule(ref)
        next_run = schedule.next()
        assert next_run > ref

    def test_successive_runs_are_ordered(self):
        """Successive calls to next() should return increasing datetimes."""
        cron = Cron("0 */6 * * *")  # every 6 hours
        schedule = cron.schedule(datetime(2026, 1, 1, 0, 0))
        times = [schedule.next() for _ in range(5)]
        assert times == sorted(times)
        assert len(set(times)) == 5  # all unique

    def test_every_minute_spacing(self):
        """'* * * * *' should produce runs exactly 1 minute apart."""
        cron = Cron("* * * * *")
        schedule = cron.schedule(datetime(2026, 1, 1, 12, 0))
        t1 = schedule.next()
        t2 = schedule.next()
        assert (t2 - t1).total_seconds() == 60

    def test_hourly_spacing(self):
        """'0 * * * *' should produce runs exactly 1 hour apart."""
        cron = Cron("0 * * * *")
        schedule = cron.schedule(datetime(2026, 1, 1, 0, 0))
        t1 = schedule.next()
        t2 = schedule.next()
        assert (t2 - t1).total_seconds() == 3600
