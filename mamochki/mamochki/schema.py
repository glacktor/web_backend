import graphene
from graphene_django.types import DjangoObjectType
from app.models import Job

class JobType(DjangoObjectType):
    class Meta:
        model = Job
        fields = ('id', 'name', 'description', 'salary', 'city', 'employer', 'status', 'photo')

class Query(graphene.ObjectType):
    job = graphene.Field(JobType, id=graphene.Int(required=True))

    def resolve_job(self, info, id):
        return Job.objects.get(pk=id)

schema = graphene.Schema(query=Query)
