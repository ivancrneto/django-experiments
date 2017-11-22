# coding=utf-8
from rest_framework import serializers
from rest_framework.fields import empty
from rest_framework.relations import HyperlinkedIdentityField
from rest_framework.reverse import reverse

from ... import conf
from ...models import Experiment


class RemoteAdminUrl(serializers.URLField):
    def __init__(self, **kwargs):
        kwargs['read_only'] = True
        super(RemoteAdminUrl, self).__init__(**kwargs)

    def to_representation(self, value):
        request = self.context.get('request', None)
        url = reverse(
            'admin:experiments_experiment_change',
            args=(value.name,),
            request=request)
        return url


class SiteSerializer(serializers.Serializer):
    def __init__(self, instance=None, data=empty, **kwargs):
        kwargs['read_only'] = True
        super(SiteSerializer, self).__init__(instance, data, **kwargs)

    def to_representation(self, instance):
        return self.get_initial()

    def get_initial(self):
        return {'name': conf.API['local']['name']}


class ExperimentSerializer(serializers.ModelSerializer):
    url = HyperlinkedIdentityField(
        view_name='experiments_api:v1:experiment',
        lookup_field='name',
    )
    admin_url = RemoteAdminUrl(source='*')
    site = SiteSerializer(source='*')

    lookup_field = 'name'
    lookup_url_kwarg = 'name'

    class Meta:
        model = Experiment
        fields = (
            'url',
            'admin_url',
            'name',
            'description',
            'alternatives',
            'state',
            'start_date',
            'end_date',
            'site',
        )
        read_only_fields = (
            'url',
            'name',
            'description',
            'alternatives',
            'start_date',
            'end_date',
        )


class ExperimentNestedSerializer(ExperimentSerializer):

    class Meta(ExperimentSerializer.Meta):
        fields = (
            'url',
            'admin_url',
            'name',
            'state',
            'start_date',
            'end_date',
        )
        read_only_fields = (
            'url',
            'name',
            'state',
            'start_date',
            'end_date',
        )
