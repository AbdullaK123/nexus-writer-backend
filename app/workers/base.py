from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore
from apscheduler.triggers.cron import CronTrigger # type: ignore
from apscheduler.job import Job  # type: ignore
from loguru import logger
from typing import Callable, Optional, Tuple


class AsyncBackgroundWorker:

    def __init__(self):
        super().__init__()
        self.scheduler = AsyncIOScheduler()
        self._running = False 

    async def start(self):
        if not self._running:
            self.scheduler.start()
            self._running = True 

    async def stop(self):
        if self._running:
            self.scheduler.shutdown()
            self._running = False

    @property
    async def is_running(self) -> bool:
        return self._running
    
    def schedule_cron_job(
        self,
        func: Callable,
        cron_expr: Optional[str] = None, 
        job_id: Optional[str] = None, 
        args: Tuple = (),
        kwargs: dict = {},
        **cron_kwargs
    ) -> Job:
        trigger = CronTrigger(**cron_kwargs) if cron_kwargs else CronTrigger.from_crontab(cron_expr)
        
        return self.scheduler.add_job(
            func,
            trigger,
            args=args,
            kwargs=kwargs or {},
            id=job_id
        )
    
    def remove_job(
        self,
        job_id
    ):
        self.scheduler.remove_job(job_id)

    def remove_all_jobs(self):
        self.scheduler.remove_all_jobs()