#!/usr/bin/env python3
"""
Test script to verify timezone functionality for daily metrics.

This script demonstrates how the timezone-aware metrics calculation works.
"""

from datetime import date, datetime, time, timedelta

import pytz


def calculate_utc_boundaries(target_date: date, user_timezone: str = "UTC"):
    """
    Calculate UTC boundaries for a date in a specific timezone.

    This mimics the logic in the metrics repository.
    """
    user_tz = pytz.timezone(user_timezone)

    # Get midnight-to-midnight in user's timezone
    local_start = user_tz.localize(datetime.combine(target_date, time.min))
    local_end = user_tz.localize(datetime.combine(target_date + timedelta(days=1), time.min))

    # Convert to UTC for querying
    date_start_utc = local_start.astimezone(pytz.UTC)
    date_end_utc = local_end.astimezone(pytz.UTC)

    return local_start, local_end, date_start_utc, date_end_utc


def main():
    """Run timezone boundary calculation tests."""
    print("=" * 80)
    print("TIMEZONE FUNCTIONALITY TEST")
    print("=" * 80)
    print()

    # Test date: December 1, 2023
    test_date = date(2023, 12, 1)

    # Test different timezones
    timezones = [
        "UTC",
        "America/Los_Angeles",  # PST/PDT (UTC-8/-7)
        "America/New_York",     # EST/EDT (UTC-5/-4)
        "Europe/London",        # GMT/BST (UTC+0/+1)
        "Asia/Tokyo",           # JST (UTC+9)
        "Australia/Sydney",     # AEDT (UTC+11/+10)
    ]

    print(f"Test Date: {test_date}")
    print()

    for tz in timezones:
        print(f"\nTimezone: {tz}")
        print("-" * 80)

        local_start, local_end, utc_start, utc_end = calculate_utc_boundaries(
            test_date, tz
        )

        print(f"  Local Start:  {local_start} ({tz})")
        print(f"  Local End:    {local_end} ({tz})")
        print(f"  UTC Start:    {utc_start} (UTC)")
        print(f"  UTC End:      {utc_end} (UTC)")

        # Calculate the duration in hours
        duration_hours = (utc_end - utc_start).total_seconds() / 3600
        print(f"  Duration:     {duration_hours} hours")

        # Show what UTC times would be queried for this "day"
        print(f"\n  Database Query Range (UTC):")
        print(f"    FROM: {utc_start.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"    TO:   {utc_end.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    print("\n" + "=" * 80)
    print("EDGE CASE: User in PST experiencing 4 PM reset issue")
    print("=" * 80)
    print()

    # The user's problem: in PST, midnight UTC is 4 PM PST
    user_tz = "America/Los_Angeles"
    utc_midnight = datetime(2023, 12, 1, 0, 0, 0, tzinfo=pytz.UTC)

    # Convert UTC midnight to PST
    pst_tz = pytz.timezone(user_tz)
    pst_time = utc_midnight.astimezone(pst_tz)

    print(f"UTC Midnight:  {utc_midnight.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"In PST:        {pst_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print()
    print("BEFORE FIX: Daily metrics reset at 4 PM PST (midnight UTC)")
    print("AFTER FIX:  Daily metrics reset at midnight PST")
    print()

    # Show the fix
    today_pst = date(2023, 11, 30)  # Nov 30 in PST
    local_start, local_end, utc_start, utc_end = calculate_utc_boundaries(
        today_pst, user_tz
    )

    print(f"User's 'Nov 30' in PST:")
    print(f"  Starts: {local_start.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"  Ends:   {local_end.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"\nDatabase will query UTC range:")
    print(f"  FROM: {utc_start.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"  TO:   {utc_end.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    print("\n" + "=" * 80)
    print("VALIDATION TEST: IANA Timezone Names")
    print("=" * 80)
    print()

    valid_timezones = [
        "America/Los_Angeles",
        "UTC",
        "Europe/London",
        "Asia/Tokyo",
    ]

    invalid_timezones = [
        "PST",
        "EST",
        "GMT",
        "Invalid/Timezone",
    ]

    print("Valid IANA timezone names:")
    for tz in valid_timezones:
        try:
            pytz.timezone(tz)
            print(f"  ✓ {tz}")
        except pytz.exceptions.UnknownTimeZoneError:
            print(f"  ✗ {tz} - ERROR")

    print("\nInvalid timezone names (will be rejected):")
    for tz in invalid_timezones:
        try:
            pytz.timezone(tz)
            print(f"  ✓ {tz} - Accepted (unexpected!)")
        except pytz.exceptions.UnknownTimeZoneError:
            print(f"  ✗ {tz} - Correctly rejected")

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
