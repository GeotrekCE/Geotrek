from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.test import TestCase
from django.contrib.auth.models import Permission
from django.core import mail

from mapentity.factories import SuperUserFactory, UserFactory

from geotrek.common.tests import CommonTest, TranslationResetMixin
from geotrek.feedback import models as feedback_models
from geotrek.feedback import factories as feedback_factories
from rest_framework.test import APIClient


class ReportViewsetMailSend(TestCase):
    def test_mail_send_on_request(self):
        self.client.post(
            '/api/en/reports/report',
            {
                'email': 'test@geotrek.local',
                'comment': 'Test comment',
                'activity': feedback_factories.ReportActivityFactory.create().pk,
                'problem_magnitude': feedback_factories.ReportProblemMagnitudeFactory.create().pk,
            })
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[1].subject, "Geotrek : Signal a mistake")
        self.assertIn("We acknowledge receipt of your feedback", mail.outbox[1].body)
        self.assertEqual(mail.outbox[1].from_email, settings.DEFAULT_FROM_EMAIL)


class ReportViewsTest(CommonTest):
    model = feedback_models.Report
    modelfactory = feedback_factories.ReportFactory
    userfactory = SuperUserFactory

    def get_bad_data(self):
        return {'geom': 'FOO'}, _('Invalid geometry value.')

    def get_good_data(self):
        return {
            'geom': '{"type": "Point", "coordinates": [0, 0]}',
            'email': 'yeah@you.com',
            'activity': feedback_factories.ReportActivityFactory.create().pk,
            'problem_magnitude': feedback_factories.ReportProblemMagnitudeFactory.create().pk,
        }

    def test_good_data_with_name(self):
        """Test report created if `name` in data"""
        data = self.get_good_data()
        data['name'] = 'Anonymous'
        self.login()
        response = self.client.post(self._get_add_url(), data)
        self.assertEqual(response.status_code, 302)
        obj = self.model.objects.last()
        self.assertEqual(obj.email, data['email'])
        self.logout()


class BaseAPITest(TestCase):
    def setUp(self):
        self.user = UserFactory(password='booh')
        perm = Permission.objects.get_by_natural_key('add_report', 'feedback', 'report')
        self.user.user_permissions.add(perm)

        self.login_url = '/login/'

    def login(self):
        response = self.client.get(self.login_url)
        csrftoken = response.cookies.get('csrftoken', '')
        response = self.client.post(self.login_url,
                                    {'username': self.user.username,
                                     'password': 'booh',
                                     'csrfmiddlewaretoken': csrftoken},
                                    allow_redirects=False)
        self.assertEqual(response.status_code, 302)


class CreateReportsAPITest(BaseAPITest):
    def setUp(self):
        super(CreateReportsAPITest, self).setUp()
        self.add_url = '/api/en/reports/report'
        self.data = {
            'geom': '{"type": "Point", "coordinates": [3, 46.5]}',
            'email': 'yeah@you.com',
            'activity': feedback_factories.ReportActivityFactory.create().pk,
            'problem_magnitude': feedback_factories.ReportProblemMagnitudeFactory.create().pk,
        }

    def post_report_data(self, data):
        client = APIClient()
        response = client.post(self.add_url, data=data,
                               allow_redirects=False)
        self.assertEqual(response.status_code, 201)

    def test_reports_can_be_created_using_post(self):
        self.post_report_data(self.data)
        self.assertTrue(feedback_models.Report.objects.filter(email='yeah@you.com').exists())
        report = feedback_models.Report.objects.get()
        self.assertAlmostEqual(report.geom.x, 700000)
        self.assertAlmostEqual(report.geom.y, 6600000)

    def test_reports_can_be_created_without_geom(self):
        self.data.pop('geom')
        self.post_report_data(self.data)
        self.assertTrue(feedback_models.Report.objects.filter(email='yeah@you.com').exists())


class ListCategoriesTest(TranslationResetMixin, BaseAPITest):
    def setUp(self):
        super(ListCategoriesTest, self).setUp()
        self.cat = feedback_factories.ReportCategoryFactory(category_it='Obstaculo')

    def test_categories_can_be_obtained_as_json(self):
        response = self.client.get('/api/en/feedback/categories.json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data[0]['id'], self.cat.id)
        self.assertEqual(data[0]['label'], self.cat.category)

    def test_categories_are_translated(self):
        response = self.client.get('/api/it/feedback/categories.json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data[0]['label'], self.cat.category_it)


class ListOptionsTest(TranslationResetMixin, BaseAPITest):
    def setUp(self):
        super(ListOptionsTest, self).setUp()
        self.activity = feedback_factories.ReportActivityFactory(activity_it='Hiking')
        self.cat = feedback_factories.ReportCategoryFactory(category_it='Obstaculo')
        self.pb_magnitude = feedback_factories.ReportProblemMagnitudeFactory(magnitude_it='Possible')

    def test_options_can_be_obtained_as_json(self):
        response = self.client.get('/api/en/feedback/options.json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['activities'][0]['id'], self.activity.id)
        self.assertEqual(data['activities'][0]['label'], self.activity.activity)
        self.assertEqual(data['categories'][0]['id'], self.cat.id)
        self.assertEqual(data['categories'][0]['label'], self.cat.category)
        self.assertEqual(data['magnitudeProblems'][0]['id'], self.pb_magnitude.id)
        self.assertEqual(data['magnitudeProblems'][0]['label'], self.pb_magnitude.magnitude)

    def test_options_are_translated(self):
        response = self.client.get('/api/it/feedback/options.json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['activities'][0]['label'], self.activity.activity_it)
        self.assertEqual(data['categories'][0]['label'], self.cat.category_it)
        self.assertEqual(data['magnitudeProblems'][0]['label'], self.pb_magnitude.magnitude_it)
