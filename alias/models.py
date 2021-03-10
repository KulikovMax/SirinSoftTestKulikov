import pytz

from datetime import datetime
from django.db import models
from django.utils import timezone


class Alias(models.Model):
    alias = models.CharField(max_length=512)
    target = models.CharField(max_length=24)
    start = models.DateTimeField()
    end = models.DateTimeField(null=True, default=None)

    def save(self, *args, **kwargs):
        # this check is used for updating existing Alias via alias_replace function.
        if Alias.objects.filter(alias=self.alias, target=self.target, start=self.start):
            super(Alias, self).save(*args, **kwargs)
        else:

            if self.end is not None:
                # int: amount of Alias objects which fulfill the condition:
                # new_alias.start <= existing_alias.start < new_alias.end
                aliases_overlapping_start = Alias.objects.filter(alias=self.alias, target=self.target,
                                                                 start__gte=self.start, start__lt=self.end).count()

                # int: amount of Alias objects which fulfill the condition:
                # new_alias.start <= existing_alias.end < new_alias.end
                aliases_overlapping_end = Alias.objects.filter(alias=self.alias, target=self.target,
                                                               end__gte=self.start, end__lt=self.end).count()

                # bool: True if there is any overlapping at start or end of new Alias
                overlapping_present = aliases_overlapping_start > 0 or aliases_overlapping_end > 0

                if overlapping_present:
                    raise ValueError("Your new Alias may cause overlap.")
                else:
                    super(Alias, self).save(*args, **kwargs)
            # For case end is None
            else:
                aliases_overlapping_start = Alias.objects.filter(alias=self.alias, target=self.target,
                                                                 start__gte=self.start).count()

                overlapping_present = aliases_overlapping_start > 0

                if overlapping_present:
                    raise ValueError("Your new Alias may cause overlap.")
                else:
                    super(Alias, self).save(*args, **kwargs)

    def __str__(self):
        if (self.start <= timezone.now() and self.end is None) or (self.start <= timezone.now() < self.end):
            return self.target
        else:
            if timezone.now() < self.start:
                raise ValueError("Alias is not active yet")
            elif timezone.now() >= self.end:
                raise ValueError("Alias is no longer active")

    def __repr__(self):
        if self.end is None or self.start <= timezone.now() < self.end:
            return self.target
        else:
            if timezone.now() < self.start:
                raise ValueError("Alias is not active yet")
            elif timezone.now() >= self.end:
                raise ValueError("Alias is no longer active")


def get_aliases(target: str, start: datetime or str, end: datetime or None):
    """Function that allows user to get all aliases of specific target in specific time range

    Args:
    :param target: The object whose aliases the user wants to get.
    :param start: The date and time(including microseconds) from which the alias is active (inclusive).
                Format for str: 'YYYY-MM-DD hh:mm:ss:us'. (notice whitespace!)
                Example for str: '2020-01-01 00:00:00:000000'.
    :param end: The date and time(including microseconds) until which the alias is active (exclusive).
                Format for str: 'YYYY-MM-DD hh:mm:ss:us'. (notice whitespace!)
                Example for str: '2020-12-31 23:59:59:999999'. (notice that this is exclusive value)

    Returns:
    :return: aliases[]
    """
    if isinstance(start, str):
        from_ = datetime.strptime(start, '%Y-%m-%d %H:%M:%S.%f')
        from_ = from_.replace(tzinfo=pytz.utc)
    elif isinstance(start, datetime):
        from_ = start.replace(tzinfo=pytz.utc)
    else:
        raise ValueError("'start' should be either datetime or str")

    query_set = Alias.objects.filter(target=target)
    aliases = list()

    if end is not None:
        if isinstance(end, str):
            to = datetime.strptime(end, '%Y-%m-%d %H:%M:%S:%f')
            to = to.replace(tzinfo=pytz.utc)
        elif isinstance(end, datetime):
            to = end.replace(tzinfo=pytz.utc)
        else:
            raise ValueError("'end' should be either datetime or str or None")
        for alias in query_set:
            if alias.start >= from_ and alias.end <= to:
                aliases.append(alias.alias)
    else:
        for alias in query_set:
            if alias.start >= from_:
                aliases.append(alias.alias)
    return aliases[:]


def alias_replace(existing_alias: Alias, replace_at: datetime, new_alias_value: str):
    """
    Function that allows user to replace existing Alias with new.
    Args:
    :param existing_alias: An Alias object that you want to replace.
    :param replace_at: Date (and time) which will be the end of existing alias and start of new Alias
    :param new_alias_value: String that will be an alias field of new Alias instance
    Return:
    :return: Alias(alias=new_alias_value, target=existing_alias.target, start=replace_at, end=None)
    """
    existing_alias.end = replace_at
    existing_alias.save(update_fields=['end'])
    Alias.objects.create(alias=new_alias_value, target=existing_alias.target, start=replace_at, end=None)
    return Alias.objects.get(alias=new_alias_value).alias
