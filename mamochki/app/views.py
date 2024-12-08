from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from django.utils import timezone
from django.http import Http404
from .models import Job, Rezume, RezumeJob
from .serializers import *
from django.conf import settings
from minio import Minio
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework.response import *
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from drf_yasg.utils import swagger_auto_schema
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly, IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from app.permissions import *
import redis
import uuid
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes, authentication_classes, action

session_storage = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)

def method_permission_classes(classes):
    def decorator(func):
        def decorated_func(self, *args, **kwargs):
            self.permission_classes = classes        
            self.check_permissions(self.request)
            return func(self, *args, **kwargs)
        return decorated_func
    return decorator

def process_file_upload(file_object: InMemoryUploadedFile, client, image_name):
    try:
        client.put_object('navy-sea', image_name, file_object, file_object.size)#semenfixисправить mamochki
        return f"http://localhost:9000/mybucket/rabota/{image_name}"
    except Exception as e:
        return {"error": str(e)}


def add_pic(new_job, pic):
    client = Minio(
        endpoint=settings.AWS_S3_ENDPOINT_URL,
        access_key=settings.AWS_ACCESS_KEY_ID,
        secret_key=settings.AWS_SECRET_ACCESS_KEY,
        secure=settings.MINIO_USE_SSL
    )
    img_obj_name = f"{new_job.id}.jpg"

    if not pic:
        return {"error": "Нет файла для изображения."}

    result = process_file_upload(pic, client, img_obj_name)

    if 'error' in result:
        return {"error": result['error']}

    return result


# View для Job (работ)
class JobList(APIView):
    model_class = Job
    serializer_class = JobSerializer

    def get(self, request, format=None):
        job_name = request.query_params.get('job_name')
        jobs = self.model_class.objects.filter(status='a')
        if job_name:
            jobs = jobs.filter(job_name__icontains=job_name)
        user = request.user
        draft_rezume_id = None
        count = 0
        if user.is_authenticated:
            draft_rezume = Rezume.objects.filter(creator=user, status='dr').first()
            if draft_rezume:
                draft_rezume_id = draft_rezume.id
                count = RezumeJob.objects.filter(rezume=draft_rezume).count()

        # serializer = self.serializer_class(ships, many=True)
        serializer = self.serializer_class(jobs, many=True, context={'is_list': True})
        response_data = {
            'jobs': serializer.data,
            'draft_rezume_id': draft_rezume_id,
            'count': count
        }
        return Response(response_data)

    @swagger_auto_schema(request_body=serializer_class)
    @method_permission_classes([IsManager])
    def post(self, request, format=None):
        pic = request.FILES.get("photo")
        data = request.data.copy()
        data.pop('photo', None)
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            job = serializer.save()
            if pic:
                pic_url = add_pic(job, pic)
                if 'error' in pic_url:
                    return Response({"error": pic_url['error']}, status=status.HTTP_400_BAD_REQUEST)
                job.photo = pic_url
                job.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class JobDetail(APIView):
    model_class = Job
    serializer_class = JobSerializer

    def get(self, request, pk, format=None):
        job = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(job)
        return Response(serializer.data)

    def post(self, request, pk, format=None):
        if request.path.endswith('/image/'):
            return self.update_image(request, pk)
        elif request.path.endswith('/draft/'):
            return self.add_to_draft(request, pk)
        raise Http404

    @swagger_auto_schema(request_body=serializer_class)
    @method_permission_classes([IsManager])
    def update_image(self, request, pk):
        job = get_object_or_404(self.model_class, pk=pk)
        pic = request.FILES.get("photo")

        if not pic:
            return Response({"error": "Файл изображения не предоставлен."}, status=status.HTTP_400_BAD_REQUEST)

        if job.photo:
            client = Minio(
                endpoint=settings.AWS_S3_ENDPOINT_URL,
                access_key=settings.AWS_ACCESS_KEY_ID,
                secret_key=settings.AWS_SECRET_ACCESS_KEY,
                secure=settings.MINIO_USE_SSL
            )
            old_img_name = job.photo.split('/')[-1]
            try:
                client.remove_object('navy-sea', old_img_name)#семенsemenисправитьfix mamochki
            except Exception as e:
                return Response({"error": f"Ошибка при удалении старого изображения: {str(e)}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        pic_url = add_pic(job, pic)
        if 'error' in pic_url:
            return Response({"error": pic_url['error']}, status=status.HTTP_400_BAD_REQUEST)

        job.photo = pic_url
        job.save()

        return Response({"message": "Изображение успешно обновлено.", "photo_url": pic_url}, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=serializer_class)
    def add_to_draft(self, request, pk):
        user = request.user
        if not user:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        job = get_object_or_404(self.model_class, pk=pk)
        draft_rezume = Rezume.objects.filter(creator=user, status='dr').first()

        if not draft_rezume:
            draft_rezume = Rezume.objects.create(
                creator=user,
                status='dr',
                created_at=timezone.now()
            )
            draft_rezume.save()

        if RezumeJob.objects.filter(rezume=draft_rezume, job=job).exists():
            return Response(data={"error": "Работа уже добавлена в черновик."}, status=status.HTTP_400_BAD_REQUEST)

        RezumeJob.objects.create(rezume=draft_rezume, job=job)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(request_body=serializer_class)
    @method_permission_classes([IsManager])
    def put(self, request, pk, format=None):
        job = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(job, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @method_permission_classes([IsManager])
    def delete(self, request, pk, format=None):
        job = get_object_or_404(self.model_class, pk=pk)
        if job.photo:
            client = Minio(
                endpoint=settings.AWS_S3_ENDPOINT_URL,
                access_key=settings.AWS_ACCESS_KEY_ID,
                secret_key=settings.AWS_SECRET_ACCESS_KEY,
                secure=settings.MINIO_USE_SSL
            )
            image_name = job.photo.split('/')[-1]
            try:
                client.remove_object('mybucket', image_name)#семенsemenисправитьfix mamochki
            except Exception as e:
                return Response({"error": f"Ошибка при удалении изображения: {str(e)}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        job.status = 'd'  # Мягкое удаление
        job.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


# View для Rezume (резюме)
class RezumeList(APIView):
    model_class = Rezume
    serializer_class = RezumeSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        user = request.user
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        status = request.query_params.get('status')

        #rezumes = self.model_class.objects.filter(creator=user).exclude(status__in=['dr', 'del'])
        if user.is_authenticated:
            if user.is_staff:
                rezumes = self.model_class.objects.all()
            else:
                rezumes = self.model_class.objects.filter(creator=user).exclude(status__in=['dr', 'del'])
        else:
            return Response({"error": "Вы не авторизованы"}, status=401)

        if date_from:
            rezumes = rezumes.filter(created_at__gte=date_from)
        if date_to:
            rezumes = rezumes.filter(created_at__lte=date_to)

        if status:
            rezumes = rezumes.filter(status=status)

        serialized_rezumes = [
            {
                **self.serializer_class(rezume, exclude_jobs=True).data,
                'creator': rezume.creator.email,
                'moderator': rezume.moderator.email if rezume.moderator else None
            }
            for rezume in rezumes
        ]

        return Response(serialized_rezumes)

    @swagger_auto_schema(request_body=serializer_class)
    @method_permission_classes([IsAdmin, IsManager])
    def put(self, request, format=None):
        user = request.user
        required_fields = ['rezume_name']
        for field in required_fields:
            if field not in request.data or request.data[field] is None:
                return Response({field: 'Это поле обязательно для заполнения.'}, status=status.HTTP_400_BAD_REQUEST)

        rezume_id = request.data.get('id')
        if rezume_id:
            rezume = get_object_or_404(self.model_class, pk=rezume_id)
            serializer = self.serializer_class(rezume, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save(moderator=user)
                return Response(serializer.data)

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            rezume = serializer.save(creator=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RezumeDetail(APIView):
    model_class = Rezume
    serializer_class = RezumeSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, format=None):
        rezume = get_object_or_404(self.model_class, pk=pk)
        if rezume.status == 'del':
            return Response({"detail": "Эта заявка удалена и недоступна для просмотра."}, status=403)
        # serializer = self.serializer_class(rezume)
        serializer = self.serializer_class(rezume, context={'is_resume': True})
        data = serializer.data
        data['creator'] = rezume.creator.email
        if rezume.moderator:
            data['moderator'] = rezume.moderator.email

        return Response(data)

    def put(self, request, pk, format=None):
        full_path = request.path

        if full_path.endswith('/form/'):#семенsemenисправитьfix
            return self.put_creator(request, pk)
        elif full_path.endswith('/complete/'):
            return self.put_moderator(request, pk)
        elif full_path.endswith('/edit/'):
            return self.put_edit(request, pk)

        return Response({"error": "Неверный путь"}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(request_body=serializer_class)
    def put_creator(self, request, pk):
        rezume = get_object_or_404(self.model_class, pk=pk)
        user = request.user

        if user == rezume.creator:

            if 'status' in request.data and request.data['status'] == 'f':
                rezume.formed_at = timezone.now()
                updated_data = request.data.copy()

                serializer = self.serializer_class(rezume, data=updated_data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            return Response({"error": "Создатель может только формировать заявку."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"error": "Отказано в доступе"}, status=status.HTTP_403_FORBIDDEN)

    @swagger_auto_schema(request_body=serializer_class)
    def put_moderator(self, request, pk):
        rezume = get_object_or_404(self.model_class, pk=pk)
        user = request.user
        if 'status' in request.data:
            status_value = request.data['status']

            # Модератор может завершить ('c') или отклонить ('r') заявку
            if status_value in ['c', 'r']:
                if rezume.status != 'f':
                    return Response({"error": "Заявка должна быть сначала сформирована."},
                                    status=status.HTTP_403_FORBIDDEN)

                if status_value == 'c':
                    rezume.completed_at = timezone.now()
                    updated_data = request.data.copy()

                serializer = self.serializer_class(rezume, data=updated_data, partial=True)
                if serializer.is_valid():
                    serializer.save(moderator=user)
                    return Response(serializer.data)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({"error": "Модератор может только завершить или отклонить заявку."},
                        status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(request_body=serializer_class)
    def put_edit(self, request, pk):
        rezume = get_object_or_404(self.model_class, pk=pk)

        serializer = self.serializer_class(rezume, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        rezume = get_object_or_404(self.model_class, pk=pk)
        if rezume.creator != request.user:
            return Response({"detail": "Только создатель может удалить заказ."}, status=403)
        if rezume.status != 'dr':
            return Response({"detail": "Данную заявку нельзя удалить."}, status=403)
        rezume.status = 'del'  # Мягкое удаление
        rezume.formed_at = timezone.now()
        rezume.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


# View для RezumeJob (вакансий в резюме)
class RezumeJobDetail(APIView):
    model_class = RezumeJob
    serializer_class = RezumeJobSerializer

    @swagger_auto_schema(request_body=serializer_class)
    def put(self, request, rezume_id, job_id, format=None):
        rezume = get_object_or_404(Rezume, pk=rezume_id)
        rezume_job = get_object_or_404(self.model_class, rezume=rezume, job__id=job_id)

        serializer = self.serializer_class(rezume_job, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, rezume_id, job_id, format=None):
        rezume = get_object_or_404(Rezume, pk=rezume_id)
        rezume_job = get_object_or_404(self.model_class, rezume=rezume, job__id=job_id)
        print(rezume_job)
        rezume_job.delete()
        return Response({"message": "Вакансия успешно удалена из резюме"}, status=status.HTTP_204_NO_CONTENT)


# View для User (пользователей)
class UserViewSet(ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    model_class = CustomUser

    def get_permissions(self):
        if self.action in ['create', 'profile']:
            permission_classes = [AllowAny]
        elif self.action in ['list']:
            permission_classes = [IsAdmin | IsManager]
        else:
            permission_classes = [IsAdmin]
        return [permission() for permission in permission_classes]

    def create(self, request):
        if self.model_class.objects.filter(email=request.data['email']).exists():
            return Response({'status': 'Exist'}, status=400)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            self.model_class.objects.create_user(
                email=serializer.data['email'],
                password=serializer.data['password'],
                is_superuser=serializer.data['is_superuser'],
                is_staff=serializer.data['is_staff']
            )
            return Response({'status': 'Success'}, status=200)
        return Response({'status': 'Error', 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['put'], permission_classes=[AllowAny])
    def profile(self, request, format=None):
        user = request.user
        if user is None:
            return Response({'error': 'Вы не авторизованы'}, status=status.HTTP_401_UNAUTHORIZED)
        serializer = self.serializer_class(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Профиль обновлен', 'user': serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@authentication_classes([])
@swagger_auto_schema(method='post', request_body=UserSerializer)
@api_view(['Post'])
@csrf_exempt
@permission_classes([AllowAny])
def login_view(request):
    username = request.data["email"] 
    password = request.data["password"]
    user = authenticate(request, email=username, password=password)
    if user is not None:
        random_key = str(uuid.uuid4())
        session_storage.set(random_key, username)
        response = HttpResponse("{'status': 'ok'}")
        response.set_cookie("session_id", random_key)
        return response
        # login(request, user)
        # return HttpResponse("{'status': 'ok'}")
    else:
        return HttpResponse("{'status': 'error', 'error': 'login failed'}")
def logout_view(request):
    session_id = request.COOKIES.get("session_id")
    if session_id:
        session_storage.delete(session_id)
        response = HttpResponse("{'status': 'ok'}")
        response.delete_cookie("session_id")
        return response
    else:
        return HttpResponse("{'status': 'error', 'error': 'no session found'}")