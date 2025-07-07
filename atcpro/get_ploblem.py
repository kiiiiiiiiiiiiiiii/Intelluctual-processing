def get_problem_page(contest_id, problem_id):
    """
    指定された問題のページを取得する関数  
    :param problem_id: 問題のID  
    :return: 問題ページのHTML  
    """
    from main import get_html
    import re

    endpoint = "https://atcoder.jp"
    
    # 解説ページの取得
    url = f"{endpoint}/contests/{contest_id}/tasks/{problem_id}/editorial"
    editorial_hub = get_html(url)
    if editorial_hub is None:
        raise ValueError(f"指定された問題のページが見つかりません: {contest_id} {problem_id}")
    
    # 解説ページIDを取得
    editorial_a = editorial_hub.find_all("a")
    for a in editorial_a:
        href = a.get("href")
        if href and re.search(r"editorial/\d+", href):
            url = a.get("href")
            break
    # 解説ページを取得
    url = f"{endpoint}/{url}"
    editorial= get_html(url)
    if editorial is None:
        raise ValueError(f"指定された問題の解説ページが見つかりません: {contest_id} {problem_id}")
    
    # 解説を取得 & 不要な要素を削除
    editorial_content = editorial.find("div", id="main-container")
    if editorial_content.find("div", id="contest-nav-tabs") is None or editorial_content.find("div", class_="clearfix") is None:
        return None
    editorial_content.find("div", id="contest-nav-tabs").decompose()  
    editorial_content.find("div", class_="clearfix").decompose()

    # コードブロックを抽出
    editorial_codes = []
    for pre in editorial_content.find_all("pre"):
        editorial_codes.append(pre.text.strip())
        pre.decompose()

    # 解説テキストを抽出
    editorial_text = editorial_content.text.strip()

    return {
        "text": editorial_text,
        "codes": editorial_codes
    }

def save_problem_page():
    """
    解説テキストとコードをJsonファイルに保存する
    """
    from main import get_detailed_problems_information, get_contests_information, get_json, set_json

    json_path = "data/problems_editorial.json"
    problem_json = get_json(json_path)
    problem_json_ids = set(problem_json.keys())

    problems = get_detailed_problems_information()
    problems_map = {problem["id"]: problem for problem in problems}
    problem_ids = {problem["id"] for problem in problems}
    
    contests = get_contests_information()
    contests = {contest["id"]: contest for contest in contests}

    # jsonに書き込まれていないもののみ取得
    search_ids = problem_ids - problem_json_ids
    # ABC175以降の問題のみを取得
    search_ids = list(filter(lambda x: contests[problems_map[x]["contest_id"]]["start_epoch_second"] >= 1597492800, search_ids))
    # 若い順にソート
    search_ids = sorted(search_ids, key=lambda x: contests[problems_map[x]["contest_id"]]["start_epoch_second"])

    for i, id in enumerate(search_ids):
        contest_id = problems_map[id]["contest_id"]
        data = get_problem_page(contest_id, id)
        problem_json.update({ id: data })
        set_json(json_path, problem_json)
        print(f"contest: {contest_id}, problem: {id} success! {(i + 1) / len(search_ids): .1%} ({i + 1}/{len(search_ids)})")

save_problem_page()