from django.core.management.base import BaseCommand
from app.models import CustomUser, Job, Rezume, RezumeJob
from datetime import datetime

class Command(BaseCommand):
    help = 'Fills the database with test data: users, jobs, resumes, and resume-job relationships'

    def handle(self, *args, **kwargs):
        # Создание пользователей
        for i in range(1, 11):
            email = f'user{i}@example.com'
            password = ''.join(str(x) for x in range(1, i + 1))
            user, created = CustomUser.objects.get_or_create(
                email=email,
            )

            if created:
                user.set_password(password)  # Устанавливаем захешированный пароль
                user.save()

                if i == 9 or i == 10:
                    user.is_staff = True
                    user.save()

                self.stdout.write(self.style.SUCCESS(f'User "{user.email}" created with password "{password}".'))
            else:
                self.stdout.write(self.style.WARNING(f'User "{user.email}" already exists.'))

        # Создание вакансий
        jobs_data = [
            {
                'name': 'Программист',
                'salary': 80000,
                'employer': 'ООО ТехноСфера',
                'city': 'Санкт-Петербург',
                'description': 'Ищем программиста для разработки и поддержки веб-приложений. Обязанности: написание кода, тестирование, работа с базами данных, участие в разработке новых функций. Условия: работа в команде, гибкий график, обучение, возможность удаленной работы.',
                'photo': 'http://localhost:9000/mybucket/rabota/7.jpg'
            },
            {
                'name': 'Повар',
                'salary': 55000,
                'employer': 'ООО Продажи Плюс',
                'city': 'Москва',
                'description': 'Требуется повар для работы в уютном ресторане. Обязанности: приготовление блюд по меню, поддержание чистоты на рабочем месте. График сменный, питание за счет компании, возможность карьерного роста.',
                'photo': 'http://localhost:9000/mybucket/rabota/8.jpg'
            },
            {
                'name': 'Бариста',
                'salary': 50000,
                'employer': 'Кофейня Ромашка',
                'city': 'Санкт-Петербург',
                'description': 'Опыт работы баристой от 6 месяцев. Знание приготовления кофейных напитков.',
                'photo': 'http://localhost:9000/mybucket/rabota/6.jpg'
            },
            {
                'name': 'Водитель такси',
                'salary': 70000,
                'employer': 'Таксопарк Быстрая машина',
                'city': 'Москва',
                'description': 'Опыт вождения от 3 лет. Отличное знание города и навигации.',
                'photo': 'http://localhost:9000/mybucket/rabota/3.jpg'
            },
            {
                'name': 'Онлайн-консультант',
                'salary': 25000,
                'employer': 'Консалтинг 24/7',
                'city': 'Москва',
                'description': 'Удалённая работа с гибким графиком, консультация клиентов через чат и почту, возможна работа с частичной занятостью.',
                'photo': 'http://localhost:9000/mybucket/rabota/2.jpg'
            },
            {
                'name': 'Копирайтер',
                'salary': 30000,
                'employer': 'Агентство "Медиа Текст"',
                'city': 'Санкт-Петербург',
                'description': 'Создание текстов для социальных сетей и сайтов, возможна частичная занятость и удалённый формат работы. Опыт написания текстов обязателен.',
                'photo': 'http://localhost:9000/mybucket/rabota/4.jpg'
            },
            {
                'name': 'Менеджер по поддержке клиентов',
                'salary': 27000,
                'employer': '"Связь-Про"',
                'city': 'Ростов-на-Дону',
                'description': 'Работа в режиме home office, консультирование клиентов по телефону и почте. Возможность гибкого графика.',
                'photo': 'http://localhost:9000/mybucket/rabota/5.jpg'
            },
            {
                'name': 'Специалист по вводу данных',
                'salary': 24000,
                'employer': 'DataTech',
                'city': 'Казань',
                'description': 'Удаленная работа с гибким графиком, ввод данных в систему компании. Требуется аккуратность и базовые навыки работы на ПК.',
                'photo': 'http://localhost:9000/mybucket/rabota/1.jpg'
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
                'description': 'Татьяна, 30 лет, мать-одиночка',
                'status': 'c',
                'creator_id': 1,
                'moderator_id': 9,
                'created_at': datetime.now(), 
                'formed_at': datetime.now(),
                'completed_at': datetime.now()
            },
            {
                'description': 'Елена, 28 лет, на последнем месяце беременности, в поисках удаленной работы',
                'status': 'f',
                'creator_id': 2,
                'created_at': datetime.now(), 
                'formed_at': datetime.now()
            },
            {
                'description': 'Анастасия, 32 года, в декретном отпуске, готова работать на частичную занятость',
                'status': 'f',
                'creator_id': 3,
                'created_at': datetime.now(),
                'formed_at': datetime.now()
            },
            {
                'description': 'Мария, 26 лет, будущая мама, ищет гибкий график работы',
                'status': 'dr',
                'creator_id': 4,
                'created_at': datetime.now()
            }
        ]

        for resume_data in resumes_data:
            resume, created = Rezume.objects.get_or_create(
                description=resume_data['description'],
                defaults={
                    'status': resume_data['status'],
                    'creator': resume_data['creator_id'],
                    'moderator': resume_data['moderator_id'],
                    'created_at': resume_data['created_at'],
                    'formed_at': resume_data['formed_at'],
                    'completed_at': resume_data['completed_at']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Resume "{resume.description}" created.'))
            else:
                self.stdout.write(self.style.WARNING(f'Resume "{resume.description}" already exists.'))

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
