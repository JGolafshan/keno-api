#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Date: 03/08/2025
Author: Joshua David Golafshan
"""


import datetime

def _transform_time(_datetime):
    """
    Private Method:
        Transforms a date in a datetime object with the correct
        time information, it also factors in daylight savings
        currently working on adding tz and dst to this function
    """
    try:
        datetime_datatype = datetime.datetime.strptime(_datetime, '%Y-%m-%d %H:%M:%S').replace(
            tzinfo=datetime.timezone.utc)
    except ValueError:
        datetime_datatype = datetime.datetime.strptime(_datetime, '%Y-%m-%d').replace(
            tzinfo=datetime.timezone.utc)
    return datetime_datatype


def _transform_keno_time(_datetime):
    """
    Private Method:
        Transforms a date in a datetime object with the correct
        time information, it also factors in daylight savings
        currently working on adding tz and dst to this function
    """
    return datetime.datetime.strptime(_datetime, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=datetime.timezone.utc)


def _calculate_time_difference(og_date, new_date):
    """
        Private Method:
        Calculates the difference in two dates
    """
    if new_date > og_date:
        time_difference = new_date - og_date
    else:
        time_difference = og_date - new_date

    return time_difference