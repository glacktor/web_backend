from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from app.models import Job, Rezume, RezumeJob

class Command(BaseCommand):
    help = 'Fills the database with test data: jobs, resumes, and resume-job relationships'

    def handle(self, *args, **kwargs):
        # Создание пользователей
        for i in range(1, 6):
            password = f'password{i}'
            user, created = User.objects.get_or_create(
                username=f'user{i}',
                defaults={'password': password}
            )
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f'User "{user.username}" created with password "{password}".'))
            else:
                self.stdout.write(self.style.WARNING(f'User "{user.username}" already exists.'))

        # Создание вакансий
        jobs_data = [
            {
                'name': 'Glep',
                'salary': 100000,
                'employer': 'ООО Ministerstvo Dao',
                'city': 'Москва',
                'description': 'Глеб (системная администрация) Стрельцов 8:00 - 22:00 UTC - em marsilies',
                'photo': 'http://localhost:9000/mybucket/rabota/marsilies.jpg'
            },
            {
                'name': 'Jeko$&$',
                'salary': 90000,
                'employer': 'Самокат DAO',
                'city': 'Ростов',
                'description': 'Опыт работы в сфере продаж от 1 года. Умение общаться с клиентами.',
                'photo': 'http://localhost:9000/mybucket/rabota/galeti.jpg'
            },
            {
                'name': 'Бариста',
                'salary': 50000,
                'employer': 'Кофейня Ромашка',
                'city': 'Санкт-Петербург',
                'description': 'Опыт работы баристой от 6 месяцев. Знание приготовления кофейных напитков.',
                'photo': 'http://localhost:9000/mybucket/rabota/barista.jpg'
            },
            {
                'name': 'Водитель такси',
                'salary': 70000,
                'employer': 'Таксопарк Быстрая машина',
                'city': 'Москва',
                'description': 'Опыт вождения от 3 лет. Отличное знание города и навигации.',
                'photo': 'http://localhost:9000/mybucket/rabota/taxi.jpg'
            },
            {
                'id': 5,
                'name': 'Онлайн-консультант',
                'salary': 25000,
                'employer': 'Консалтинг 24/7',
                'city': 'Москва',
                'description': 'Удалённая работа с гибким графиком, консультация клиентов через чат и почту, возможна работа с частичной занятостью.',
                'photo': 'http://localhost:9000/mybucket/rabota/consultant.jpg'
            },
            {
                'id': 6,
                'name': 'Копирайтер',
                'salary': 30000,
                'employer': 'Агентство "Медиа Текст"',
                'city': 'Санкт-Петербург',
                'description': 'Создание текстов для социальных сетей и сайтов, возможна частичная занятость и удалённый формат работы. Опыт написания текстов обязателен.',
                'photo': 'http://localhost:9000/mybucket/rabota/copywriter.jpg'
            },
            {
                'id': 7,
                'name': 'Менеджер по поддержке клиентов',
                'salary': 27000,
                'employer': '"Связь-Про"',
                'city': 'Ростов-на-Дону',
                'description': 'Работа в режиме home office, консультирование клиентов по телефону и почте. Возможность гибкого графика.',
                'photo': 'http://localhost:9000/mybucket/rabota/support.jpg'
            },
            {
                'id': 8,
                'name': 'Специалист по вводу данных',
                'salary': 24000,
                'employer': 'DataTech',
                'city': 'Казань',
                'description': 'Удаленная работа с гибким графиком, ввод данных в систему компании. Требуется аккуратность и базовые навыки работы на ПК.',
                'photo': 'http://localhost:9000/mybucket/rabota/data_entry.jpg'
            }
        ]

        for job_data in jobs_data:
            job, created = Job.objects.get_or_create(
                name=job_data['name'],
                defaults={
                    'salary': job_data['salary'],
                    'employer': job_data['employer'],
                    'city': job_data['city'],
                    'description': job_data['description'],
                    'photo': job_data['photo'],
                    'status': 'a'
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Job "{job.name}" added.'))
            else:
                self.stdout.write(self.style.WARNING(f'Job "{job.name}" already exists.'))

        # Создание резюме
        resumes_data = [
            {
                'rezume_description': 'Татьяна, 30 лет, мать-одиночка',
                'status': 'f',
                'creator_id': 1
            },
            {
                'rezume_description': 'Елена, 28 лет, на последнем месяце беременности, в поисках удаленной работы',
                'status': 'dr',
                'creator_id': 2
            },
            {
                'rezume_description': 'Анастасия, 32 года, в декретном отпуске, готова работать на частичную занятость',
                'status': 'dr',
                'creator_id': 3
            },
            {
                'rezume_description': 'Мария, 26 лет, будущая мама, ищет гибкий график работы',
                'status': 'dr',
                'creator_id': 4
            }
        ]

        for resume_data in resumes_data:
            resume, created = Rezume.objects.get_or_create(
                rezume_description=resume_data['rezume_description'],
                defaults={
                    'status': resume_data['status'],
                    'creator_id': resume_data['creator_id']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Resume "{resume.rezume_description}" created.'))
            else:
                self.stdout.write(self.style.WARNING(f'Resume "{resume.rezume_description}" already exists.'))



        # Связывание резюме и вакансий через таблицу RezumeJob
        rezume_jobs_data = [
            {'rezume_id': 1, 'job_id': 1, 'experience': 1},
            {'rezume_id': 1, 'job_id': 2, 'experience': 2},
            {'rezume_id': 1, 'job_id': 3, 'experience': 2},
            {'rezume_id': 1, 'job_id': 4, 'experience': 1},
            {'rezume_id': 2, 'job_id': 1, 'experience': 1},
            {'rezume_id': 2, 'job_id': 3, 'experience': 3},
            {'rezume_id': 3, 'job_id': 5, 'experience': 2},
            {'rezume_id': 3, 'job_id': 6, 'experience': 1},
            {'rezume_id': 4, 'job_id': 7, 'experience': 3},
            {'rezume_id': 4, 'job_id': 8, 'experience': 3}
        ]

        for rezume_job_data in rezume_jobs_data:
            rezume_job, created = RezumeJob.objects.get_or_create(
                rezume_id=rezume_job_data['rezume_id'],
                job_id=rezume_job_data['job_id'],
                defaults={'experience': rezume_job_data['experience']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'RezumeJob entry for resume {rezume_job_data["rezume_id"]}, job {rezume_job_data["job_id"]} created.'))
            else:
                self.stdout.write(self.style.WARNING(f'RezumeJob entry for resume {rezume_job_data["rezume_id"]}, job {rezume_job_data["job_id"]} already exists.'))

