from django.shortcuts import render, get_object_or_404, redirect
from .models import Job, Rezume, RezumeJob
from django.db import connection


def add_job_to_rezume(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    user = request.user

    try:
        rezume = Rezume.objects.get(creator=user, status='dr')
    except Rezume.DoesNotExist:
        rezume = Rezume.objects.create(creator=user, status='dr')

    rezume_job, created = RezumeJob.objects.get_or_create(rezume=rezume, job=job)
    rezume_job.save()

    return redirect('index')


def delete_rezume(request, rezume_id):
    with connection.cursor() as cursor:
        cursor.execute("UPDATE app_rezume SET status = 'del' WHERE id = %s", [rezume_id])

    return redirect('index')


def index(request):
    job_name = request.GET.get('job')
    first_rezume = Rezume.objects.first()
    count_jobs = RezumeJob.objects.filter(rezume=first_rezume).count() if first_rezume else 0
    user = request.user
    curr_rezume = Rezume.objects.filter(creator=user, status='dr').first()
    if curr_rezume:
        rezume_info = {
            'id': curr_rezume.id,
            'count': Rezume.objects.get_total_jobs(curr_rezume)
        }
    else:
        rezume_info = None

    if job_name:
        jobs = Job.objects.filter(job_name__icontains=job_name)
        return render(request, 'index.html', {
            "jobs": jobs,
            'query': job_name,
            "rezume": rezume_info
        })
    else:
        jobs = Job.objects.all()
        return render(request, 'index.html', {"jobs": jobs, "rezume": rezume_info})


def job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    return render(request, 'job.html', {"job": job})


def rezume(request, rezume_id):
    try:
        curr_rezume = Rezume.objects.get(id=rezume_id)
        if curr_rezume.status == 'del':
            raise Rezume.DoesNotExist
    except Rezume.DoesNotExist:
        return render(request, 'rezume.html', {"error_message": "Нельзя просмотреть резюме."})

    rezume_data = get_object_or_404(Rezume, id=rezume_id)

    liked_jobs = Job.objects.filter(likedjob__liked=rezume_data)

    experience = {}
    for rezume_job in RezumeJob.objects.filter(rezume=rezume_data):
        experience[rezume_job.job.id] = rezume_job.experience

    context = {
        'rezume': rezume_data,
        #'battle_name': rezume_data.fight_name,
        'liked_jobs': liked_jobs,
        'experience': experience,
        'rezume_description': rezume_data.description
    }

    return render(request, 'rezume.html', context)


# def get_jobs_by_ids(job_ids):
#     return [job for job in JOBS if job['id'] in job_ids]
#
#
# def rezume(request, rezume_id):
#     rezume_data = next((rezume for rezume in REZUME_DATA if rezume['id'] == rezume_id), None)
#
#     if rezume_data:
#         liked_jobs = get_jobs_by_ids(rezume_data['jobs'])
#
#         context = {
#             'description': rezume_data['description'],
#             'liked_jobs': liked_jobs,
#             'experience': rezume_data['experience'],
#         }
#
#         return render(request, 'rezume.html', context)
