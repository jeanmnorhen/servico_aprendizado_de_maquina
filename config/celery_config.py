import os
from celery import Celery
from kombu import Queue

# Configure Celery
celery_app = Celery(
    "unified_ai_tasks",
    broker=os.environ.get("REDIS_URL", "redis://redis:6379/0"),
    backend=os.environ.get("REDIS_URL", "redis://redis:6379/0"),
    task_default_queue='default'
)

celery_app.conf.task_queues = (
    Queue('text_queue', routing_key='text_task'),
    Queue('vision_queue', routing_key='vision_task'),
)

celery_app.conf.task_routes = {
    'workers.text_worker.process_animation_script': {'queue': 'text_queue', 'routing_key': 'text_task'},
    'workers.text_worker.generate_product_description': {'queue': 'text_queue', 'routing_key': 'text_task'},
    'workers.vision_worker.monitor_sprites_directory': {'queue': 'vision_queue', 'routing_key': 'vision_task'},
    'workers.vision_worker.process_product_image': {'queue': 'vision_queue', 'routing_key': 'vision_task'},
}

celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    beat_schedule={
        'monitor-sprites-every-30-seconds': {
            'task': 'workers.vision_worker.monitor_sprites_directory',
            'schedule': 30.0,
            'args': (),
        },
    },
)

celery_app.conf.imports = (
    'workers.text_worker',
    'workers.vision_worker',
)
