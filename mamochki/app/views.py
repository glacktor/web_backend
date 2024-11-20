from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from django.utils import timezone
from django.http import Http404
from .models import Job, Rezume, RezumeJob
from .serializers import JobSerializer, RezumeSerializer, RezumeJobSerializer, UserSerializer
from django.conf import settings
from minio import Minio
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework.response import *
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout


class UserSingleton:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            try:
                cls._instance = User.objects.get(id=2)
            except User.DoesNotExist:
                cls._instance = None
        return cls._instance

    @classmethod
    def clear_instance(cls, user):
        pass


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
        user = UserSingleton.get_instance()
        draft_rezume_id = None
        count = 0
        if user:
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

    def add_to_draft(self, request, pk):
        user = UserSingleton.get_instance()
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

    def put(self, request, pk, format=None):
        job = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(job, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
                client.remove_object('navy-sea', image_name)#семенsemenисправитьfix mamochki
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

    def get(self, request, format=None):
        user = UserSingleton.get_instance()

        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        status = request.query_params.get('status')

        rezumes = self.model_class.objects.filter(creator=user).exclude(status__in=['dr', 'del'])

        if date_from:
            rezumes = rezumes.filter(created_at__gte=date_from)
        if date_to:
            rezumes = rezumes.filter(created_at__lte=date_to)

        if status:
            rezumes = rezumes.filter(status=status)

        serialized_rezumes = [
            {
                **self.serializer_class(rezume, exclude_jobs=True).data,
                'creator': rezume.creator.username,
                'moderator': rezume.moderator.username
            }
            for rezume in rezumes
        ]

        return Response(serialized_rezumes)

    def put(self, request, format=None):
        user = UserSingleton.get_instance()
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

    def get(self, request, pk, format=None):
        rezume = get_object_or_404(self.model_class, pk=pk)
        if rezume.status == 'del':
            return Response({"detail": "Эта заявка удалена и недоступна для просмотра."}, status=403)
        # serializer = self.serializer_class(rezume)
        serializer = self.serializer_class(rezume, context={'is_resume': True})
        data = serializer.data
        data['creator'] = rezume.creator.username
        if rezume.moderator:
            data['moderator'] = rezume.moderator.username

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

    def put_creator(self, request, pk):
        rezume = get_object_or_404(self.model_class, pk=pk)
        user = UserSingleton.get_instance()

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

    def put_moderator(self, request, pk):
        rezume = get_object_or_404(self.model_class, pk=pk)
        user = UserSingleton.get_instance()

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

    def put_edit(self, request, pk):
        rezume = get_object_or_404(self.model_class, pk=pk)

        serializer = self.serializer_class(rezume, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        rezume = get_object_or_404(self.model_class, pk=pk)
        rezume.status = 'del'  # Мягкое удаление
        rezume.formed_at = timezone.now()
        rezume.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


# View для RezumeJob (кораблей в сражениях)
class RezumeJobDetail(APIView):
    model_class = RezumeJob
    serializer_class = RezumeJobSerializer

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
        rezume_job.delete()
        return Response({"message": "Корабль успешно удален из сражения"}, status=status.HTTP_204_NO_CONTENT)


# View для User (пользователей)
class UserView(APIView):
    def post(self, request, action, format=None):
        if action == 'register':
            serializer = UserSerializer(data=request.data)
            if serializer.is_valid():
                validated_data = serializer.validated_data
                user = User(
                    username=validated_data['username'],
                    email=validated_data['email']
                )
                user.set_password(request.data.get('password'))
                user.save()
                return Response({'message': 'Регистрация успешна'}, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif action == 'authenticate':
            username = request.data.get('username')
            password = request.data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                user_data = UserSerializer(user).data
                return Response({
                    'message': 'Аутентификация успешна',
                    'user': user_data
                }, status=status.HTTP_200_OK)
            return Response({'error': 'Неправильное имя пользователя или пароль'}, status=status.HTTP_400_BAD_REQUEST)

        elif action == 'logout':
            return Response({'message': 'Вы вышли из системы'}, status=status.HTTP_200_OK)

        return Response({'error': 'Неверное действие'}, status=status.HTTP_400_BAD_REQUEST)

    # Обновление данных профиля пользователя
    def put(self, request, action, format=None):
        if action == 'profile':
            user = UserSingleton.get_instance()
            if user is None:
                return Response({'error': 'Вы не авторизованы'}, status=status.HTTP_401_UNAUTHORIZED)

            serializer = UserSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'message': 'Профиль обновлен', 'user': serializer.data}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({'error': 'Некорректное действие'}, status=status.HTTP_400_BAD_REQUEST)