"""Read curated learning resources and game showcases without executing their content."""
import json
import re
from pathlib import Path
from urllib.parse import urlsplit


def text_field(value, name, limit=2000):
    if not isinstance(value, str) or len(value) > limit:
        raise ValueError(f"{name}: {limit}文字以内の文字列にしてください。")


def text_list(value, name, limit=12):
    if not isinstance(value, list) or len(value) > limit:
        raise ValueError(f"{name}: {limit}項目以内の配列にしてください。")
    for item in value:
        text_field(item, name, 300)


def resolve_inside(root, value):
    text_field(value, "パス", 500)
    file = (root / value).resolve()
    if not file.is_relative_to(root.resolve()):
        raise ValueError("資料のパスが指定フォルダの外に出ています。")
    return file


def validate_profile(data):
    if not isinstance(data, dict) or type(data.get("schema_version")) is not int or data.get("schema_version") != 1:
        raise ValueError("schema_versionは1にしてください。")
    if data.get("status") not in {"draft", "sample", "published"}:
        raise ValueError("statusはdraft / sample / publishedにしてください。")
    for key in ("summary", "audience"):
        text_field(data.get(key), key)
    for key in ("how_to_play", "flow", "learning_goals", "limitations"):
        text_list(data.get(key, []), key)
    technologies = data.get("technologies", [])
    if not isinstance(technologies, list) or len(technologies) > 10:
        raise ValueError("technologiesは10項目以内にしてください。")
    for item in technologies:
        if not isinstance(item, dict):
            raise ValueError("technologiesの各項目はオブジェクトにしてください。")
        text_field(item.get("name"), "技術名", 60)
        text_field(item.get("role"), "技術の役割", 300)
    questions = data.get("questions", [])
    if not isinstance(questions, list) or len(questions) > 10:
        raise ValueError("questionsは10問以内の配列にしてください。")
    for item in questions:
        if not isinstance(item, dict):
            raise ValueError("questionsの各項目はオブジェクトにしてください。")
        for key in ("question", "hint", "answer"):
            text_field(item.get(key), f"questions.{key}", 1000)
    creation = data.get("creation", {})
    if not isinstance(creation, dict):
        raise ValueError("creationはオブジェクトにしてください。")
    for key in ("goal", "ai_role", "human_role", "evidence"):
        text_field(creation.get(key, ""), f"creation.{key}")
    refs = data.get("code_refs", [])
    if not isinstance(refs, list) or len(refs) > 6:
        raise ValueError("code_refsは6箇所以内にしてください。")
    for ref in refs:
        if not isinstance(ref, dict):
            raise ValueError("code_refsの各項目はオブジェクトにしてください。")
        for key in ("file", "label", "explanation"):
            text_field(ref.get(key), f"code_refs.{key}")
        start, end = ref.get("start_line"), ref.get("end_line")
        if type(start) is not int or type(end) is not int or not 1 <= start <= end or end - start >= 30:
            raise ValueError("コード引用は1箇所につき1〜30行にしてください。")
        if Path(ref["file"]).suffix.lower() not in {".py", ".js", ".html", ".css"} or any(part.startswith(".") for part in Path(ref["file"]).parts):
            raise ValueError("コード引用は公開する.py / .js / .html / .cssだけを指定してください。")
    slides = data.get("slides")
    if not isinstance(slides, list) or len(slides) != 3:
        raise ValueError("slidesはちょうど3ページにしてください。")
    for slide in slides:
        if not isinstance(slide, dict):
            raise ValueError("slidesの各項目はオブジェクトにしてください。")
        text_field(slide.get("title"), "スライド見出し", 60)
        text_field(slide.get("message"), "スライドの要点", 160)
        text_list(slide.get("points", []), "スライド本文", 3)
        for point in slide.get("points", []):
            text_field(point, "スライド本文", 100)
        if "code_ref" in slide and (type(slide["code_ref"]) is not int or not 0 <= slide["code_ref"] < len(refs)):
            raise ValueError("スライドのcode_refは、登録済みコード引用の番号を0から指定してください。")
        text_field(slide.get("notes", ""), "発表メモ", 2000)
    screenshot = data.get("screenshot", "")
    text_field(screenshot, "screenshot", 200)
    if screenshot and not re.fullmatch(r"/showcase/assets/[a-z0-9-]+\.(png|jpg|webp)", screenshot):
        raise ValueError("screenshotは/showcase/assets/内の画像を指定してください。")
    sources = data.get("sources", [])
    if not isinstance(sources, list) or len(sources) > 10:
        raise ValueError("sourcesは10項目以内の配列にしてください。")
    for source in sources:
        if not isinstance(source, dict):
            raise ValueError("sourcesの各項目はオブジェクトにしてください。")
        text_field(source.get("label"), "出典名", 100)
        url = source.get("url")
        text_field(url, "出典URL", 1000)
        if urlsplit(url).scheme not in {"http", "https"} or not urlsplit(url).netloc:
            raise ValueError("出典URLはhttpかhttpsで指定してください。")
    return data


def placeholder_profile(game):
    return {
        "schema_version": 1, "status": "draft", "summary": game.get("description", ""),
        "audience": "高専1・2年生を中心に、初めてコードを読む人", "how_to_play": [],
        "technologies": [], "flow": [], "learning_goals": [], "questions": [], "code_refs": [],
        "creation": {"evidence": "制作記録と本人の学習成果を登録すると、ここに表示できます。"},
        "slides": [
            {"title": "私が作ったゲーム", "message": "［本人がゲームのねらいを記入］", "points": ["［遊び方と完成画面］"], "notes": ""},
            {"title": "使った技術と仕組み", "message": "［本人が説明できる仕組みを記入］", "points": ["［コードの関数名と役割］"], "notes": ""},
            {"title": "AIとの制作と学び", "message": "［実際に確かめた学習成果を記入］", "points": ["［AIに頼んだこと］", "［自分で確認・変更したこと］", "［まだ分からないこと］"], "notes": ""}
        ], "limitations": ["このページは記入前のひな形です。学習成果の提出はまだありません。"], "sources": []
    }


def load_profile(root, game):
    if not game.get("profile"):
        data = placeholder_profile(game)
    else:
        path = resolve_inside(root, game["profile"])
        if path.suffix.lower() != ".json" or path.stat().st_size > 256_000:
            raise ValueError("紹介資料は256KB以下のJSONにしてください。")
        data = validate_profile(json.loads(path.read_text(encoding="utf-8-sig")))
    source_root = resolve_inside(root, data.get("source_root", game.get("path", ".")))
    excerpts = []
    for ref in data.get("code_refs", []):
        file = resolve_inside(source_root, ref["file"])
        if file.stat().st_size > 512_000:
            raise ValueError("コード引用元が大きすぎます。")
        lines = file.read_text(encoding="utf-8-sig").splitlines()
        if ref["end_line"] > len(lines):
            raise ValueError(f"コード引用の行番号を確認してください: {ref['file']}")
        excerpts.append({**ref, "code": "\n".join(lines[ref["start_line"] - 1:ref["end_line"]])})
    return {**data, "code_refs": excerpts}


LEARNING_FILES = {
    "student-guide.md", "teacher-guide.md", "workbook.md", "submission-guide.md",
    "prompts/01-readability.md", "prompts/02-study-guide.md", "prompts/03-coach.md", "prompts/04-presentation.md"
}


def learning_file(root, name):
    if name not in LEARNING_FILES:
        raise ValueError("この学習資料は見つかりません。")
    return resolve_inside(root / "learning", name)


def load_curriculum(root):
    data = json.loads((root / "learning/curriculum.json").read_text(encoding="utf-8-sig"))
    for step in data["steps"]:
        step["prompt_text"] = learning_file(root, step["prompt_file"]).read_text(encoding="utf-8-sig")
    return data
