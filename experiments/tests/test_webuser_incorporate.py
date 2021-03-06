from django.http import HttpResponse
from django.test import TestCase, RequestFactory
from django.contrib.sessions.backends.db import SessionStore as DatabaseSession

from unittest import TestSuite

from experiments import conf
from experiments.experiment_counters import ExperimentCounter
from experiments.middleware import ExperimentsRetentionMiddleware
from experiments.signal_handlers import transfer_enrollments_to_user
from experiments.utils import DummyUser, SessionUser, AuthenticatedUser, participant
from experiments.models import Experiment, ENABLED_STATE, Enrollment

from django.contrib.auth import get_user_model

TEST_ALTERNATIVE = 'blue'
EXPERIMENT_NAME = 'backgroundcolor'


class WebUserIncorporateTestCase(object):
    def __init__(self, *args, **kwargs):
        super(WebUserIncorporateTestCase, self).__init__(*args, **kwargs)
        self.experiment_counter = ExperimentCounter()

    def test_can_incorporate(self):
        self.incorporating.incorporate(self.incorporated)

    def test_incorporates_enrollment_from_other(self):
        if not self._has_data():
            return

        try:
            experiment = Experiment.objects.create(name=EXPERIMENT_NAME, state=ENABLED_STATE)
            self.incorporated.set_alternative(EXPERIMENT_NAME, TEST_ALTERNATIVE)
            self.incorporating.incorporate(self.incorporated)
            self.assertEqual(self.incorporating.get_alternative(EXPERIMENT_NAME), TEST_ALTERNATIVE)
        finally:
            self.experiment_counter.delete(experiment)

    def _has_data(self):
        return not isinstance(self.incorporated, DummyUser) and not isinstance(self.incorporating, DummyUser)


def dummy(incorporating):
    return DummyUser()


def anonymous(incorporating):
    return SessionUser(session=DatabaseSession())


def authenticated(incorporating):
    User = get_user_model()
    return AuthenticatedUser(user=User.objects.create(username=['incorporating_user', 'incorporated_user'][incorporating]))


class Dummy2DummyIncorporateTestCase(WebUserIncorporateTestCase, TestCase):

    def setUp(self):
        super(Dummy2DummyIncorporateTestCase, self).setUp()
        self.incorporating = dummy(True)
        self.incorporated = dummy(False)


class Dummy2AnonymousIncorporateTestCase(WebUserIncorporateTestCase, TestCase):

    def setUp(self):
        super(Dummy2AnonymousIncorporateTestCase, self).setUp()
        self.incorporating = dummy(True)
        self.incorporated = anonymous(False)


class Dummy2AuthenticatedIncorporateTestCase(WebUserIncorporateTestCase, TestCase):

    def setUp(self):
        super(Dummy2AuthenticatedIncorporateTestCase, self).setUp()
        self.incorporating = dummy(True)
        self.incorporated = authenticated(False)


class Anonymous2DummyIncorporateTestCase(WebUserIncorporateTestCase, TestCase):

    def setUp(self):
        super(Anonymous2DummyIncorporateTestCase, self).setUp()
        self.incorporating = anonymous(True)
        self.incorporated = dummy(False)


class Anonymous2AnonymousIncorporateTestCase(WebUserIncorporateTestCase, TestCase):

    def setUp(self):
        super(Anonymous2AnonymousIncorporateTestCase, self).setUp()
        self.incorporating = anonymous(True)
        self.incorporated = anonymous(False)


class Anonymous2AuthenticatedIncorporateTestCase(WebUserIncorporateTestCase, TestCase):

    def setUp(self):
        super(Anonymous2AuthenticatedIncorporateTestCase, self).setUp()
        self.incorporating = anonymous(True)
        self.incorporated = authenticated(False)


class Authenticated2DummyIncorporateTestCase(WebUserIncorporateTestCase, TestCase):

    def setUp(self):
        super(Authenticated2DummyIncorporateTestCase, self).setUp()
        self.incorporating = authenticated(True)
        self.incorporated = dummy(False)


class Authenticated2AnonymousIncorporateTestCase(WebUserIncorporateTestCase, TestCase):

    def setUp(self):
        super(Authenticated2AnonymousIncorporateTestCase, self).setUp()
        self.incorporating = authenticated(True)
        self.incorporated = anonymous(False)


class Authenticated2AuthenticatedIncorporateTestCase(WebUserIncorporateTestCase, TestCase):

    def setUp(self):
        super(Authenticated2AuthenticatedIncorporateTestCase, self).setUp()
        self.incorporating = authenticated(True)
        self.incorporated = authenticated(False)


class IncorporateTestCase(TestCase):
    def setUp(self):
        self.experiment = Experiment.objects.create(name=EXPERIMENT_NAME, state=ENABLED_STATE)
        self.experiment_counter = ExperimentCounter()

        User = get_user_model()
        self.user = User.objects.create(username='incorporate_user')
        self.user.is_confirmed_human = True

        request_factory = RequestFactory()
        self.request = request_factory.get('/')
        self.request.session = DatabaseSession()
        participant(self.request).confirm_human()

    def tearDown(self):
        self.experiment_counter.delete(self.experiment)

    def _login(self):
        self.request.user = self.user
        transfer_enrollments_to_user(None, self.request, self.user)

    def test_visit_incorporate(self):
        alternative = participant(self.request).enroll(self.experiment.name, ['alternative'])

        ExperimentsRetentionMiddleware().process_response(self.request, HttpResponse())

        self.assertEqual(
            dict(self.experiment_counter.participant_goal_frequencies(self.experiment,
                                                                      alternative,
                                                                      participant(self.request)._participant_identifier()))[conf.VISIT_NOT_PRESENT_COUNT_GOAL],
            1
        )

        self.assertFalse(Enrollment.objects.all().exists())
        self._login()

        self.assertTrue(Enrollment.objects.all().exists())
        self.assertIsNotNone(Enrollment.objects.all()[0].last_seen)
        self.assertEqual(
            dict(self.experiment_counter.participant_goal_frequencies(self.experiment,
                                                                      alternative,
                                                                      participant(self.request)._participant_identifier()))[conf.VISIT_NOT_PRESENT_COUNT_GOAL],
            1
        )
        self.assertEqual(self.experiment_counter.goal_count(self.experiment, alternative, conf.VISIT_NOT_PRESENT_COUNT_GOAL), 1)
        self.assertEqual(self.experiment_counter.participant_count(self.experiment, alternative), 1)

