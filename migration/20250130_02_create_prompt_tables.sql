-- プロンプト関連テーブル作成マイグレーション
-- 実行日: 2025-01-30
-- 説明: プロンプトマスタとカクテル-プロンプト関連テーブルを作成

-- 1. promptsテーブルの作成
CREATE TABLE IF NOT EXISTS prompts (
    id SERIAL PRIMARY KEY,
    prompt_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    prompt_text TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. cocktail_promptsテーブルの作成（カクテルとプロンプトの関連）
CREATE TABLE IF NOT EXISTS cocktail_prompts (
    id SERIAL PRIMARY KEY,
    cocktail_id INTEGER NOT NULL REFERENCES cocktails(id) ON DELETE CASCADE,
    prompt_id INTEGER NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,
    prompt_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(cocktail_id, prompt_type)
);

-- デフォルトプロンプトの挿入
INSERT INTO prompts (prompt_type, title, description, prompt_text, is_active)
VALUES 
(
    'recipe',
    'デフォルトレシピ生成プロンプト',
    'カクテルレシピ生成用のベースプロンプト',
    'あなたはプロのバーテンダーです。以下のシロップ情報を参考に、入力された情報からカクテル風の名前（日本語で20文字以内）、そのカクテルのコンセプト文（日本語で1文）、生成AIでカクテルの画像を生成するためのメインカラー（液体の色）を表現する文章とメインカラーのRGB値、およびレシピ（シロップ名と比率のリスト、合計25%以内、色や味のイメージに合うように最大4種まで混ぜてOK）を考えてください。',
    TRUE
),
(
    'image',
    'デフォルト画像生成プロンプト',
    'カクテル画像生成用のベースプロンプト',
    '背景は完全な透明（透過PNG）、カクテル以外は描かず、カクテルそのものだけをリアルな質感の写真風イラストとして生成してください。必ず生成画像の液体部分の色が指定されたメインカラーのRGB値の色味に近くなるようにしてください',
    TRUE
)
ON CONFLICT DO NOTHING;

-- 実行完了ログ
SELECT 'Prompt tables created successfully' as status;