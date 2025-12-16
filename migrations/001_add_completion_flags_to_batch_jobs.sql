-- Migration: 001_add_completion_flags_to_batch_jobs.sql
-- Description: Add agent_completed and modelops_recommendation_completed flags to batch_jobs table
-- Date: 2025-12-16
-- Purpose: Support AND logic for done condition (Agent completion AND ModelOps recommendation completion)

-- Add agent_completed flag
ALTER TABLE batch_jobs
ADD COLUMN IF NOT EXISTS agent_completed BOOLEAN DEFAULT FALSE;

-- Add modelops_recommendation_completed flag
ALTER TABLE batch_jobs
ADD COLUMN IF NOT EXISTS modelops_recommendation_completed BOOLEAN DEFAULT FALSE;

-- Create index for faster queries on completion flags
CREATE INDEX IF NOT EXISTS idx_batch_jobs_completion_flags
ON batch_jobs(agent_completed, modelops_recommendation_completed);

-- Update existing rows to set both flags to TRUE if status is 'done' or 'failed'
-- (Backward compatibility for existing completed jobs)
UPDATE batch_jobs
SET agent_completed = TRUE,
    modelops_recommendation_completed = TRUE
WHERE status IN ('done', 'failed', 'done-a');

COMMENT ON COLUMN batch_jobs.agent_completed IS 'Agent 워크플로우 완료 여부 (Phase 2 리포트 생성 완료)';
COMMENT ON COLUMN batch_jobs.modelops_recommendation_completed IS 'ModelOps recommendation API 완료 여부 (후보지 추천 완료)';
