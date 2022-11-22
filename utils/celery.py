from celery import Celery


def make_celery(name: str, conf: dict) -> Celery:
    celery = Celery(name)
    celery.conf.update(conf)

    return celery
