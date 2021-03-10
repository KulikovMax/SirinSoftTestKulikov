import datetime
import random

from django.test import TestCase
from django.utils import timezone

from alias.models import Alias, get_aliases, alias_replace


class AliasModelTests(TestCase):

    def test_create_new_alias(self):
        """
        Trying to create new_alias object should return True if new Alias instance was created
        :return: True
        """

        new_alias = Alias.objects.create(alias='new-alias', target='new-target', start=timezone.now(),
                                         end=timezone.now() + datetime.timedelta(days=30))
        self.assertIs(new_alias is not None, True)

    def test_create_new_alias_not_available_yet(self):
        """
        Trying to get new_alias.alias should raise ValueError with message "Alias is not active yet" if current time
        is less than new_alias.start value
        :raise: ValueError("Alias is not active yet")
        """
        new_alias = Alias.objects.create(alias='new-alias', target='new-target',
                                         start=timezone.now() + datetime.timedelta(days=1),
                                         end=timezone.now() + datetime.timedelta(days=30))
        with self.assertRaisesMessage(ValueError, "Alias is not active yet"):
            print(Alias.objects.get(alias=new_alias.alias))

    def test_create_new_alias_no_longer_available(self):
        """
        Trying to get new_alias.alias should raise ValueError with message "Alias is no longer active"
        if current time is bigger or equal than new_alias.end value
        :raise: ValueError("Alias is no longer active")
        """
        new_alias = Alias.objects.create(alias='new-alias', target='new-target',
                                         start=timezone.now() - datetime.timedelta(days=1),
                                         end=timezone.now())
        with self.assertRaisesMessage(ValueError, "Alias is no longer active"):
            print(Alias.objects.get(alias=new_alias.alias))

    def test_end_is_none(self):
        """
        Trying to get new_alias.target should return a target at any time.
        :return: new_alias.target
        """
        new_alias = Alias.objects.create(alias='new-alias', target='new-target',
                                         start=timezone.now()-datetime.timedelta(days=random.randrange(0, 100)))
        self.assertEqual(Alias.objects.get(alias=new_alias.alias).target, new_alias.target)

    def test_end_is_exclusive(self):
        """
        Trying to create a second_alias with second_alias.start = first_alias.end should not raise error.
        :return: Nothing
        """
        first_alias = Alias.objects.create(alias='some-alias', target='some-target',
                                           start=timezone.now()-datetime.timedelta(days=50),
                                           end=timezone.now())
        second_alias = Alias.objects.create(alias='some-alias', target='some-target',
                                            start=first_alias.end,
                                            end=None)
        self.assertIsNotNone(second_alias)

    def test_two_same_aliases_of_the_same_target(self):
        """
        Trying to create two same aliases of the same target at the different points of time should not raise any error.
        :return: [first_alias.alias, first_alias.target], [second_alias.alias, second_alias.target]
        """
        first_alias = Alias.objects.create(alias='some-alias', target='some-target',
                                           start=timezone.now()-datetime.timedelta(days=30),
                                           end=timezone.now()-datetime.timedelta(days=15))
        second_alias = Alias.objects.create(alias='some-alias', target='some-target',
                                            start=timezone.now(),
                                            end=timezone.now() + datetime.timedelta(days=1))
        self.assertEqual([first_alias.alias, first_alias.target], [second_alias.alias, second_alias.target])

    def test_overlap_at_start(self):
        """
        Trying to create new alias with target of already existing alias and start<=existing_alias.start<end
        :raise: ValueError
        """
        valid_alias = Alias.objects.create(alias='some-alias', target='some-target',
                                           start=timezone.now(), end=timezone.now()+datetime.timedelta(days=50))
        with self.assertRaisesMessage(ValueError, "Your new Alias may cause overlap."):
            Alias.objects.create(alias=valid_alias.alias, target=valid_alias.target,
                                 start=valid_alias.start - datetime.timedelta(days=1),
                                 end=valid_alias.end - datetime.timedelta(days=1))

    def test_overlap_at_end(self):
        """
        Trying to create new alias with target of already existing alias and
        existing_alias.start <= start <= existing_alias.end < end
        :raise: ValueError
        """
        valid_alias = Alias.objects.create(alias='some-alias', target='some-target',
                                           start=timezone.now(), end=timezone.now() + datetime.timedelta(days=50))
        with self.assertRaisesMessage(ValueError, "Your new Alias may cause overlap."):
            Alias.objects.create(alias=valid_alias.alias, target=valid_alias.target,
                                 start=valid_alias.start + datetime.timedelta(days=1),
                                 end=valid_alias.end + datetime.timedelta(days=1))

    def test_get_aliases_returns_one_value(self):
        """
        Trying to use get_aliases function on target that has only one alias should return list with one element.
        :return: aliases[0]
        """
        new_alias = Alias.objects.create(alias='some-alias', target='some-target', start=timezone.now(), end=None)
        self.assertEqual(get_aliases(new_alias.target, new_alias.start, new_alias.end)[0], new_alias.alias)

    def test_get_aliases_returns_two_values(self):
        """
        Trying to use get_aliases function on target that has two aliases should return list with two elements.
        :return: aliases = ['some-alias', 'another-alias']
        """
        Alias.objects.create(alias='some-alias', target='some-target', start=timezone.now(), end=None)
        Alias.objects.create(alias='another-alias', target='some-target', start=timezone.now(), end=None)
        self.assertEqual(get_aliases('some-target', timezone.now() - datetime.timedelta(hours=1), None),
                         ['some-alias', 'another-alias'])

    def test_get_aliases_with_str(self):
        """
        Trying to pass start argument of get_aliases() as str should not break function execution.
        :return: new_alias.alias
        """
        new_alias = Alias.objects.create(alias='some-alias', target='some-target', start=timezone.now(), end=None)
        self.assertEqual(get_aliases(new_alias.target, '2020-01-01 0:0:0.0', None)[0], new_alias.alias)

    def test_get_aliases_with_datetime(self):
        """
        Trying to pass start argument of get_aliases() as datetime should not break function execution.
        :return: new_alias.alias
        """
        new_alias = Alias.objects.create(alias='some-alias', target='some-target', start=timezone.now(), end=None)
        self.assertEqual(get_aliases(new_alias.target, datetime.datetime(2020, 1, 1), None)[0], new_alias.alias)

    def test_alias_replace_end_is_date(self):
        """
        Trying to replace existing_alias with end as date type should not break function execution.
        :return: new_alias.alias
        """
        first_alias = Alias.objects.create(alias='first-alias', target='some-new-target',
                                           start=timezone.now(),
                                           end=timezone.now() + datetime.timedelta(days=30))
        self.assertEqual(alias_replace(first_alias, timezone.now()+datetime.timedelta(days=20), 'second-alias'),
                         Alias.objects.get(alias='second-alias', target=first_alias.target).alias)

    def test_alias_replace_end_is_none(self):
        """
        Trying to replace existing_alias with end as None should not break function execution.
        :return: True
        """
        # first_alias.end = None (by default)
        first_alias = Alias.objects.create(alias='first-alias', target='some-new-target',
                                           start=timezone.now())
        alias_replace(first_alias, timezone.now() + datetime.timedelta(days=20), 'second-alias')
        self.assertIsNotNone(first_alias.end)
