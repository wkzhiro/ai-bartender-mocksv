-- アンケート関連テーブル作成マイグレーション
-- 実行日: 2025-01-30
-- 説明: アンケート機能のためのテーブル群を作成

-- 1. surveysテーブルの作成（アンケートマスタ）
CREATE TABLE IF NOT EXISTS surveys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID REFERENCES events(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. survey_questionsテーブルの作成（質問マスタ）
CREATE TABLE IF NOT EXISTS survey_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    survey_id UUID REFERENCES surveys(id) ON DELETE CASCADE,
    question_type VARCHAR(50) NOT NULL CHECK (question_type IN ('text', 'single_choice', 'multiple_choice')),
    question_text TEXT NOT NULL,
    is_required BOOLEAN DEFAULT false,
    display_order INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. survey_question_optionsテーブルの作成（選択肢マスタ）
CREATE TABLE IF NOT EXISTS survey_question_options (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id UUID REFERENCES survey_questions(id) ON DELETE CASCADE,
    option_text VARCHAR(255) NOT NULL,
    display_order INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. survey_responsesテーブルの作成（アンケート回答）
CREATE TABLE IF NOT EXISTS survey_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    survey_id UUID REFERENCES surveys(id) ON DELETE CASCADE,
    cocktail_id INTEGER REFERENCES cocktails(id) ON DELETE SET NULL,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. survey_answersテーブルの作成（個別回答）
CREATE TABLE IF NOT EXISTS survey_answers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    response_id UUID REFERENCES survey_responses(id) ON DELETE CASCADE,
    question_id UUID REFERENCES survey_questions(id) ON DELETE CASCADE,
    answer_text TEXT,
    selected_option_ids UUID[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 実行完了ログ
SELECT 'Survey tables created successfully' as status;