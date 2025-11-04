import redis
from typing import Dict, List, Optional
from app.core.config import settings


class JobManager:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )

    def generate_job_id(self, interview_id: str, question_id: str) -> str:
        """jobId 생성: interview_id + question_id"""
        return f"{interview_id}_{question_id}"

    def add_job(self, interview_id: str, question_id: str, celery_task_id: str) -> str:
        """새로운 작업 추가"""
        job_id = self.generate_job_id(interview_id, question_id)
        job_data = {
            "interview_id": interview_id,
            "question_id": question_id,
            "celery_task_id": celery_task_id,
            "status": "PENDING",
            "created_at": ""
        }
        
        # Redis에 작업 정보 저장
        self.redis_client.hset(f"job:{job_id}", mapping=job_data)
        
        # 인터뷰별 작업 목록에 추가
        self.redis_client.sadd(f"interview_jobs:{interview_id}", job_id)
        
        return job_id

    def update_job_status(self, job_id: str, status: str, result: Optional[Dict] = None):
        """작업 상태 업데이트"""
        self.redis_client.hset(f"job:{job_id}", "status", status)
        
        if result:
            import json
            self.redis_client.hset(f"job:{job_id}", "result", json.dumps(result))

    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """작업 상태 조회"""
        job_data = self.redis_client.hgetall(f"job:{job_id}")
        if not job_data:
            return None
            
        # result가 JSON 문자열인 경우 파싱
        if "result" in job_data and job_data["result"]:
            import json
            try:
                job_data["result"] = json.loads(job_data["result"])
            except json.JSONDecodeError:
                pass
                
        return job_data

    def get_interview_jobs(self, interview_id: str) -> List[Dict]:
        """특정 인터뷰의 모든 작업 조회"""
        job_ids = self.redis_client.smembers(f"interview_jobs:{interview_id}")
        jobs = []
        
        for job_id in job_ids:
            job_status = self.get_job_status(job_id)
            if job_status:
                jobs.append(job_status)
                
        return jobs

    def check_all_jobs_completed(self, interview_id: str) -> bool:
        """특정 인터뷰의 모든 작업이 완료되었는지 확인"""
        jobs = self.get_interview_jobs(interview_id)
        
        if not jobs:
            return True
            
        for job in jobs:
            if job.get("status") not in ["SUCCESS", "FAILURE"]:
                return False
                
        return True

    def cleanup_jobs(self, interview_id: str):
        """특정 인터뷰의 모든 작업 데이터를 Redis에서 정리"""
        job_ids = self.redis_client.smembers(f"interview_jobs:{interview_id}")
        if not job_ids:
            print(f"[JobManager] {interview_id} 관련 작업 없음")
            return

        # 각 job 키 삭제
        for job_id in job_ids:
            self.redis_client.delete(f"job:{job_id}")

        # 인터뷰별 작업 목록 삭제
        self.redis_client.delete(f"interview_jobs:{interview_id}")

        print(f"[JobManager] {interview_id} 관련 모든 작업 정리 완료 ✅")


# 싱글톤 인스턴스
job_manager = JobManager()

