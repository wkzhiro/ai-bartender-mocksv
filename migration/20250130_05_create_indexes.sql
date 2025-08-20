-- インデックス作成マイグレーション
-- 実行日: 2025-01-30
-- 説明: パフォーマンス最適化のためのインデックスを作成

-- 基本テーブルのインデックス
CREATE INDEX IF NOT EXISTS idx_cocktails_order_id ON cocktails(order_id);
CREATE INDEX IF NOT EXISTS idx_cocktails_event_id ON cocktails(event_id);
CREATE INDEX IF NOT EXISTS idx_cocktails_created_at ON cocktails(created_at);
CREATE INDEX IF NOT EXISTS idx_cocktails_is_visible ON cocktails(is_visible);
CREATE INDEX IF NOT EXISTS idx_cocktails_violation_reports_count ON cocktails(violation_reports_count);

CREATE INDEX IF NOT EXISTS idx_events_name ON events(name);
CREATE INDEX IF NOT EXISTS idx_events_is_active ON events(is_active);
CREATE INDEX IF NOT EXISTS idx_events_created_at ON events(created_at);

CREATE INDEX IF NOT EXISTS idx_poured_cocktails_created_at ON poured_cocktails(created_at);
CREATE INDEX IF NOT EXISTS idx_poured_cocktails_name ON poured_cocktails(name);

-- プロンプト関連のインデックス
CREATE INDEX IF NOT EXISTS idx_prompts_type ON prompts(prompt_type);
CREATE INDEX IF NOT EXISTS idx_prompts_is_active ON prompts(is_active);

CREATE INDEX IF NOT EXISTS idx_cocktail_prompts_cocktail_id ON cocktail_prompts(cocktail_id);
CREATE INDEX IF NOT EXISTS idx_cocktail_prompts_prompt_id ON cocktail_prompts(prompt_id);
CREATE INDEX IF NOT EXISTS idx_cocktail_prompts_type ON cocktail_prompts(prompt_type);

-- 違反報告のインデックス
CREATE INDEX IF NOT EXISTS idx_violation_reports_cocktail_id ON violation_reports(cocktail_id);
CREATE INDEX IF NOT EXISTS idx_violation_reports_status ON violation_reports(status);
CREATE INDEX IF NOT EXISTS idx_violation_reports_reported_at ON violation_reports(reported_at);

-- アンケート関連のインデックス
CREATE INDEX IF NOT EXISTS idx_surveys_event_id ON surveys(event_id);
CREATE INDEX IF NOT EXISTS idx_surveys_is_active ON surveys(is_active);
CREATE INDEX IF NOT EXISTS idx_surveys_start_date ON surveys(start_date);
CREATE INDEX IF NOT EXISTS idx_surveys_end_date ON surveys(end_date);
CREATE INDEX IF NOT EXISTS idx_surveys_created_at ON surveys(created_at);

CREATE INDEX IF NOT EXISTS idx_survey_questions_survey_id ON survey_questions(survey_id);
CREATE INDEX IF NOT EXISTS idx_survey_questions_display_order ON survey_questions(survey_id, display_order);
CREATE INDEX IF NOT EXISTS idx_survey_questions_type ON survey_questions(question_type);

CREATE INDEX IF NOT EXISTS idx_survey_question_options_question_id ON survey_question_options(question_id);
CREATE INDEX IF NOT EXISTS idx_survey_question_options_display_order ON survey_question_options(question_id, display_order);

CREATE INDEX IF NOT EXISTS idx_survey_responses_survey_id ON survey_responses(survey_id);
CREATE INDEX IF NOT EXISTS idx_survey_responses_cocktail_id ON survey_responses(cocktail_id);
CREATE INDEX IF NOT EXISTS idx_survey_responses_submitted_at ON survey_responses(submitted_at);

CREATE INDEX IF NOT EXISTS idx_survey_answers_response_id ON survey_answers(response_id);
CREATE INDEX IF NOT EXISTS idx_survey_answers_question_id ON survey_answers(question_id);

-- 実行完了ログ
SELECT 'Indexes created successfully' as status;