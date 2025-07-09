-- プロンプトテーブル作成SQL
-- 1. プロンプトマスタテーブル
CREATE TABLE IF NOT EXISTS prompts (
    id SERIAL PRIMARY KEY,
    prompt_type VARCHAR(50) NOT NULL, -- 'recipe' or 'image'
    title VARCHAR(255) NOT NULL,
    description TEXT,
    prompt_text TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. カクテルとプロンプトの中間テーブル
CREATE TABLE IF NOT EXISTS cocktail_prompts (
    id SERIAL PRIMARY KEY,
    cocktail_id INTEGER NOT NULL REFERENCES cocktails(id) ON DELETE CASCADE,
    prompt_id INTEGER NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(cocktail_id, prompt_id)
);

-- 3. インデックス作成
CREATE INDEX IF NOT EXISTS idx_prompts_type ON prompts(prompt_type);
CREATE INDEX IF NOT EXISTS idx_prompts_active ON prompts(is_active);
CREATE INDEX IF NOT EXISTS idx_cocktail_prompts_cocktail_id ON cocktail_prompts(cocktail_id);
CREATE INDEX IF NOT EXISTS idx_cocktail_prompts_prompt_id ON cocktail_prompts(prompt_id);

-- 4. デフォルトプロンプトの挿入
INSERT INTO prompts (prompt_type, title, description, prompt_text) VALUES
('recipe', 'デフォルトレシピ生成プロンプト', 'カクテルレシピ生成用のベースプロンプト', 'あなたはプロのバーテンダーです。以下のシロップ情報を参考に、入力された情報からカクテル風の名前（日本語で20文字以内）、そのカクテルのコンセプト文（日本語で1文）、生成AIでカクテルの画像を生成するためのメインカラー（液体の色）を表現する文章とメインカラーのRGB値、およびレシピ（シロップ名と比率のリスト、合計25%以内、色や味のイメージに合うように最大4種まで混ぜてOK）を考えてください。'),
('image', 'デフォルト画像生成プロンプト', 'カクテル画像生成用のベースプロンプト', '背景は完全な透明（透過PNG）、カクテル以外は描かず、カクテルそのものだけをリアルな質感の写真風イラストとして生成してください。必ず生成画像の液体部分の色が指定されたメインカラーのRGB値の色味に近くなるようにしてください'),
('recipe', 'クリエイティブレシピプロンプト', 'より創造的なカクテルレシピ生成用', 'あなたは世界的に有名なクリエイティブバーテンダーです。常識にとらわれず、ユニークで印象的なカクテルを作成してください。'),
('image', 'アーティスティック画像プロンプト', 'よりアーティスティックな画像生成用', 'アーティスティックで幻想的な雰囲気のカクテル画像を生成してください。照明効果や色彩の表現にこだわった、まるでアートのような仕上がりにしてください。');