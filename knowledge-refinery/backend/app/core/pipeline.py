import asyncio
import uuid
import uuid as uuid_pkg
import traceback
from datetime import datetime
from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import shutil
import os

from app.models.entry import KnowledgeEntry
from app.models.profile import UserProfile
from app.models.pipeline_log import PipelineLog
from app.models.attachment import Attachment
from app.services.openrouter import OpenRouterClient
from app.services.extractor import Extractor
from app.services.verifier import Verifier
from app.services.analyzer import Analyzer
from app.services.md_writer import MDWriter
from app.services.preprocessor import Preprocessor
from app.services.tag_engine import TagEngine
from app.core.config import settings

# In-memory store for task progress (to be polled by frontend)
_task_states: dict[str, dict] = {}

class TaskState:
    def __init__(self, entry_id: str, mode: str):
        self.task_id = str(uuid.uuid4())
        self.entry_id = entry_id
        self.state = {
            "task_id": self.task_id,
            "entry_id": entry_id,
            "status": "processing",
            "current_stage": "extract",
            "mode": mode,
            "stages": {
                "extract": {"status": "pending", "duration_ms": None, "cost_usd": None},
                "verify_grok": {"status": "skipped" if mode == "quick" else "pending", "duration_ms": None, "cost_usd": None},
                "verify_gemini": {"status": "skipped" if mode == "quick" else "pending", "duration_ms": None, "cost_usd": None},
                "analyze": {"status": "pending", "duration_ms": None, "cost_usd": None},
            },
            "total_cost_usd": 0.0,
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": None,
        }
        _task_states[self.task_id] = self.state

    def set_stage(self, stage: str, status: str, duration: int = None, cost: float = None):
        if stage in self.state["stages"]:
            self.state["stages"][stage]["status"] = status
            if duration is not None:
                self.state["stages"][stage]["duration_ms"] = duration
            if cost is not None:
                self.state["stages"][stage]["cost_usd"] = cost
                self.state["total_cost_usd"] += cost
        if stage in ("extract", "verify", "analyze"):
            self.state["current_stage"] = stage

    def set_completed(self):
        self.state["status"] = "completed"
        self.state["current_stage"] = "done"
        self.state["completed_at"] = datetime.utcnow().isoformat()

    def set_failed(self, error: str):
        self.state["status"] = "failed"
        self.state["error"] = error

class PipelineOrchestrator:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.client = OpenRouterClient()
        self.preprocessor = Preprocessor()
        self.extractor = Extractor(self.client)
        self.verifier = Verifier(self.client)
        self.analyzer = Analyzer(self.client)
        self.md_writer = MDWriter()
        self.tag_engine = TagEngine()

    async def _get_active_profile(self) -> str:
        res = await self.db.execute(select(UserProfile).where(UserProfile.is_active == True))
        profile = res.scalar_one_or_none()
        if profile:
            return profile.profile_prompt
        return "你是一个具有商业头脑的技术战略分析师。" # Minimal fallback

    async def run(self, entry_id: uuid_pkg.UUID, input_data: dict, task_state: TaskState):
        mode = task_state.state["mode"]
        logs_to_add = []
        attachments_to_add = []
        try:
            # Preprocess
            processed = await self.preprocessor.process(input_data)
            
            # Save attachment if it's an image
            if processed["type"] == "image":
                original_file_path = input_data.get("file_path")
                if original_file_path and os.path.exists(original_file_path):
                    att_dir = os.path.join(settings.ATTACHMENTS_PATH, str(entry_id))
                    os.makedirs(att_dir, exist_ok=True)
                    att_filename = os.path.basename(original_file_path)
                    att_dest = os.path.join(att_dir, att_filename)
                    shutil.copy2(original_file_path, att_dest)
                    
                    att_record = Attachment(
                        entry_id=entry_id,
                        file_type="image",
                        file_path=f"/attachments/{entry_id}/{att_filename}",
                        original_name=att_filename,
                        file_size=os.path.getsize(att_dest)
                    )
                    attachments_to_add.append(att_record)

            # Stage 1: extract
            task_state.set_stage("extract", "running")
            start = datetime.utcnow()
            stage1_result, t_in, t_out, cost1 = await self.extractor.extract(processed)
            dur1 = int((datetime.utcnow() - start).total_seconds() * 1000)
            
            log1 = PipelineLog(entry_id=entry_id, stage="extract", model_used=self.extractor.model, input_tokens=t_in, output_tokens=t_out, cost_usd=cost1, duration_ms=dur1, status="success")
            logs_to_add.append(log1)
            task_state.set_stage("extract", "completed", dur1, cost1)

            # Stage 2: verify
            stage2_result = None
            confidence_penalty = 0.0
            if mode == "deep":
                task_state.set_stage("verify", "running")
                task_state.set_stage("verify_grok", "running")
                task_state.set_stage("verify_gemini", "running")
                
                grok_task = self.verifier.verify_grok(stage1_result)
                gemini_task = self.verifier.verify_gemini(stage1_result)
                
                start_v = datetime.utcnow()
                results = await asyncio.gather(grok_task, gemini_task, return_exceptions=True)
                dur_v = int((datetime.utcnow() - start_v).total_seconds() * 1000)
                
                grok_res = results[0] if not isinstance(results[0], Exception) else None
                gemini_res = results[1] if not isinstance(results[1], Exception) else None
                
                if isinstance(results[0], Exception):
                    task_state.set_stage("verify_grok", "failed", dur_v, 0)
                    logs_to_add.append(PipelineLog(entry_id=entry_id, stage="verify_grok", model_used=self.verifier.model_grok, duration_ms=dur_v, status="failed", error_message=str(results[0])))
                elif grok_res:
                    task_state.set_stage("verify_grok", "completed", dur_v, grok_res[3])
                    logs_to_add.append(PipelineLog(entry_id=entry_id, stage="verify_grok", model_used=self.verifier.model_grok, input_tokens=grok_res[1], output_tokens=grok_res[2], cost_usd=grok_res[3], duration_ms=dur_v, status="success", raw_response=grok_res[0]))

                if isinstance(results[1], Exception):
                    task_state.set_stage("verify_gemini", "failed", dur_v, 0)
                    logs_to_add.append(PipelineLog(entry_id=entry_id, stage="verify_gemini", model_used=self.verifier.model_gemini, duration_ms=dur_v, status="failed", error_message=str(results[1])))
                elif gemini_res:
                    task_state.set_stage("verify_gemini", "completed", dur_v, gemini_res[3])
                    logs_to_add.append(PipelineLog(entry_id=entry_id, stage="verify_gemini", model_used=self.verifier.model_gemini, input_tokens=gemini_res[1], output_tokens=gemini_res[2], cost_usd=gemini_res[3], duration_ms=dur_v, status="success", raw_response=gemini_res[0]))

                if not grok_res and not gemini_res:
                    confidence_penalty = 0.2
                    task_state.set_stage("verify", "failed")
                else:
                    stage2_result = self.verifier.merge_results(grok_res, gemini_res)
                    task_state.set_stage("verify", "completed")

            # Stage 3: analyze
            task_state.set_stage("analyze", "running")
            start = datetime.utcnow()
            profile = await self._get_active_profile()
            
            markdown_body, metadata, a_in, a_out, a_cost = await self.analyzer.analyze(
                stage1_result=stage1_result,
                stage2_result=stage2_result,
                profile_prompt=profile,
                confidence_penalty=confidence_penalty,
            )
            dur3 = int((datetime.utcnow() - start).total_seconds() * 1000)
            log3 = PipelineLog(entry_id=entry_id, stage="analyze", model_used=self.analyzer.model, input_tokens=a_in, output_tokens=a_out, cost_usd=a_cost, duration_ms=dur3, status="success")
            logs_to_add.append(log3)
            task_state.set_stage("analyze", "completed", dur3, a_cost)

            # Metadata adjustments & MD generation
            tags = await self.tag_engine.process_tags(self.db, metadata.get("tags", []))
            for t in tags:
                t.usage_count += 1
                
            md_filename = await self.md_writer.write(
                entry_id=str(entry_id),
                stage1_result=stage1_result,
                analysis_body=markdown_body,
                metadata_result=metadata,
                mode=mode,
                source_type=input_data.get("input_type", "text"),
                source_url=input_data.get("url")
            )
            
            # Save into KnowledgeEntry
            entry = KnowledgeEntry(
                id=entry_id,
                title=stage1_result.get("title", "Untitled")[:500],
                slug=md_filename.replace(".md", "")[:500],
                category=stage1_result.get("category", "other")[:50],
                md_file_path=md_filename,
                input_type=input_data.get("input_type", "text")[:20],
                source_url=input_data.get("url"),
                confidence=metadata.get("confidence", 0.0),
                maturity=metadata.get("maturity", "seed")[:20],
                pipeline_mode=mode,
                actionability=metadata.get("actionability", "medium")[:10],
                review_notes=metadata.get("review_notes"),
                tags=tags
            )
            self.db.add(entry)
            self.db.add_all(logs_to_add)
            self.db.add_all(attachments_to_add)
            await self.db.commit()

            task_state.set_completed()

        except Exception as e:
            await self.db.rollback()
            task_state.set_failed(traceback.format_exc())
            print(f"Pipeline error for entry {entry_id}: {traceback.format_exc()}")
            raise
