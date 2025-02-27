from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Job, Rezume, RezumeJob, CustomUser


class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ['id', 'name', 'description', 'salary', 'city', 'employer', 'status', 'photo']#семенsemenисправитьfix

    def __init__(self, *args, **kwargs):
        # Получаем контекст запроса
        super(JobSerializer, self).__init__(*args, **kwargs)
        context = self.context

        # Если это запрос списка, исключаем поле description
        if context.get('is_list', False):
            self.fields.pop('description')

    def get_fields(self):
        fields = super().get_fields()

        if self.context.get('is_fight', False):
            return {
                'job_name': fields['job_name'],
                'photo': fields['photo']
            }

        return fields


class RezumeJobSerializer(serializers.ModelSerializer):
    job = JobSerializer(read_only=True)

    class Meta:
        model = RezumeJob
        fields = ['job', 'experience']#семенsemenисправитьfix


class RezumeSerializer(serializers.ModelSerializer):
    jobs = RezumeJobSerializer(many=True, read_only=True, source='rezumejob_set')

    class Meta:
        model = Rezume
        fields = ['id', 'description', 'review', 'status', 'created_at', 'formed_at', 'completed_at', 'creator',
                  'moderator', 'jobs']#семенsemenисправитьfix

    def __init__(self, *args, **kwargs):
        # Получаем контекст из сериализатора
        exclude_jobs = kwargs.pop('exclude_jobs', False)
        super(RezumeSerializer, self).__init__(*args, **kwargs)

        if exclude_jobs:
            self.fields.pop('jobs', None)


class UserSerializer(serializers.ModelSerializer):
    is_staff = serializers.BooleanField(default=False, required=False)
    is_superuser = serializers.BooleanField(default=False, required=False)
    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'is_staff', 'is_superuser']