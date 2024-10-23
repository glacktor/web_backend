from django.shortcuts import render
from test_data import JOBS
from test_data import REZUME_DATA


def index(request):
    job_name = request.GET.get('job')
    first_rezume = REZUME_DATA[0]
    count_jobs = len(first_rezume['jobs'])
    if job_name:
        jobs = []
        for job in JOBS:
            if job_name.lower() in job['name'].lower():
                jobs.append(job)
        return render(request, 'index.html', {
            "jobs": jobs,
            'query': job_name,
            "rezume": 1,
            "count": count_jobs
            })

    else:
        return render(request, 'index.html', {"jobs": JOBS, "rezume": 1, "count": count_jobs})


def job(request, job_id):
    for work in JOBS:
        if work['id'] == job_id:
            job = work
            break
    return render(request, 'job.html', {"job": job})


def get_jobs_by_ids(job_ids):
    return [job for job in JOBS if job['id'] in job_ids]


def rezume(request, rezume_id):
    rezume_data = next((rezume for rezume in REZUME_DATA if rezume['id'] == rezume_id), None)
    
    if rezume_data:
        liked_jobs = get_jobs_by_ids(rezume_data['jobs'])

        context = {
            'description': rezume_data['description'],
            'liked_jobs': liked_jobs,
            'employers': rezume_data['employers'],
        }

        return render(request, 'rezume.html', context)
