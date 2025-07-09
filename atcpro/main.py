
import datetime
import json
import os
import time
import re
from bs4 import BeautifulSoup
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv
from gui import windowShow
load_dotenv()

TEST = False

def get_api(url, params=None):
    if TEST:
        return None
    try:
        time.sleep(1)
        res = requests.get(url, params=params)
        res.raise_for_status()
        data = res.json()
        return data
    except requests.exceptions.RequestException as err:
        print(f"Error: {err}")

def use_gemini(text, TEST=False):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={os.getenv('GEMINI_API_KEY')}"
    headers = {
        "Content-Type": "applicatoin/json"
    }
    text =  """
            マークダウン記法を使わずに、プレーンテキストで回答してください。
            箇条書きは使わず、通常の文章で記述してください。
            コードブロックは含めないでください。
            太字や斜体などの装飾は不要です。
            """ + text

    data = {
        "contents": [
            {
                "parts": [
                    { "text": text }
                ]
            }
        ]
    }

    try:
        if TEST:
            response = get_json("data/gemini.json")
            result = response
        else:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            response.raise_for_status()
            result = response.json()

        if "candidates" in result and len(result["candidates"]) > 0:
            generated_text = result["candidates"][0]["content"]["parts"][0]["text"]
            return generated_text
        else:
            print("テキストを生成できませんでした。")
            if "promptFeedback" in result:
                print(f"プロンプトフィードバック: {result['promptFeedback']}")
    except requests.exceptions.RequestException as e:
        print(f"APIリクエスト中にエラーが発生しました: {e}")
    except json.JSONDecodeError:
        print(f"JSONでコードエラー: {response.text}")

def get_html(url):
    if TEST:
        return None
    try:
        time.sleep(1)
        res = requests.get(url)
        soup = BeautifulSoup(res.text, 'html.parser')
        return soup
    except requests.exceptions.RequestException as err:
        print(f"Error: {err}")

def get_text(path):
    module_path = os.path.abspath(os.path.dirname(__file__))
    with open(f"{module_path}/{path}", encoding="utf-8") as f:
        return f.read()

def get_json(path):
    module_path = os.path.abspath(os.path.dirname(__file__))
    with open(f"{module_path}/{path}", encoding="utf-8") as f:
        return json.load(f)

def set_json(path, data):
    module_path = os.path.abspath(os.path.dirname(__file__))
    with open(f"{module_path}/{path}", "w",encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_contests_information():
    if TEST:
        return get_json("./data/contests.json")
    return get_api("https://kenkoooo.com/atcoder/resources/contests.json")

def get_problems_information():
    return get_api("https://kenkoooo.com/atcoder/resources/problems.json")

def get_detailed_problems_information():
    if TEST: 
        return get_json("./data/merged-problems.json")
    return get_api("https://kenkoooo.com/atcoder/resources/merged-problems.json")

def get_pairs_of_contests_and_problems():
    return get_api("https://kenkoooo.com/atcoder/resources/contest-problem.json")

def get_accepted_count(user):
    params = {"user": user}
    return get_api("https://kenkoooo.com/atcoder/atcoder-api/v3/user/ac_rank", params)

def get_rated_point_sum(user):
    params = {"user": user}
    return get_api("https://kenkoooo.com/atcoder/atcoder-api/v3/user/rated_point_sum_rank", params)

def get_accepted_count_for_each_language(user):
    params = {"user": user}
    return get_api("https://kenkoooo.com/atcoder/atcoder-api/v3/user/language_rank", params)

def get_user_submissions(user, from_second):
    if TEST:
        return get_json("./data/submissions.json")
    params = {"user": user, "from_second": from_second}
    return get_api("https://kenkoooo.com/atcoder/atcoder-api/v3/user/submissions", params)

def get_submissions_at_the_time(from_second):
    return get_api(f"https://kenkoooo.com/atcoder/atcoder-api/v3/from/{from_second}")

def time2epoch(time_str):
    """
    ### Convert a time string to epoch time. 
    Example: "2023/10/01 12:34:56" -> 1696150496
    """
    dt_obj = datetime.datetime.strptime(time_str, "%Y/%m/%d %H:%M:%S")
    return int(dt_obj.timestamp())

def get_difficulties():
    """
    問題の難易度
    """
    return get_api("https://kenkoooo.com/atcoder/resources/problem-models.json")

USER_HISTORY_KEY = ("date", "contest_id", "rank", "pafs", "rating", "diff")
def get_histories(user, N=10):
    """
    直近の10コンテストの情報を取得  
    Args: user(str): userID  
    Returns: { date, contest_id, rank, pafs, rating, diff }[]
    """

    if TEST:
        html = get_text("./data/history.html")
        soup = BeautifulSoup(html, 'html.parser')
    else:
        soup = get_html(f"https://atcoder.jp/users/{user}/history?contestType=algo")
    trs = soup.find_all("tr")
    ret = []
    for tr in trs[::-1]:
        tds = tr.find_all("td")
        if (len(tds) < 6):
            continue
        infos = {}
        for key, td in zip(USER_HISTORY_KEY, tds): 
            if key == "date":
                infos[key] =  td.get("data-order")
            elif key == "contest_id":
                infos[key] = td.find("a").get("href").split("/")[-1]
            elif key == "rank":
                infos[key] = td.text.strip()
            elif key == "pafs":
                infos[key] = td.text.strip()
            elif key == "rating" or key == "diff":
                if td.text.strip() == "-":
                    infos[key] = None
                else:
                    infos[key] = int(td.text.strip())
        ret.append(infos)
        if len(ret) >= N:
            break
    return ret

def get_submissions_merge_contest_info(user, histories=None):
    """
    直近のユーザーの提出物とコンテストIDを紐づけて取得  
    { contest_id: submission[] }
    """
    if histories is None:
        histories = get_histories(user) # 直近のコンテスト履歴を取得
    histories.sort(key=lambda x: time2epoch(x["date"])) # 日付順にソート
    contest_datas = get_contests_information() # すべてのコンテスト情報を取得
    submissions = []
    ret = {}
    for history in histories:
        if len(history) < 6:
            continue

        # コンテストデータをフィルターで取得
        contest = list(filter(lambda x: x["id"] == history["contest_id"], contest_datas))[0]
        if contest is None:
            continue

        # コンテストの開始時刻と終了時刻を取得
        start_epoch = int(contest["start_epoch_second"])
        end_epoch = start_epoch + int(contest["duration_second"])
        
        # コンテスト開始時間に合わせて提出物を取得(改めて必要な場合のみ取得)
        if len(submissions) == 0 or submissions[-1]["epoch_second"] < end_epoch:
            submissions = get_user_submissions(user, start_epoch)
            print(f"epoch_seciond: {start_epoch} ~ {end_epoch}, submissions: {len(submissions)}")

        submissions_filter = list(filter(lambda x: x["contest_id"] == history["contest_id"] and int(x["epoch_second"]) >= start_epoch and int(x["epoch_second"]) <= end_epoch, submissions))
        ret[history["contest_id"]] = submissions_filter
    return ret

def get_similarity_problems(problem_id, N=3, difficulty=None, least_diff=0):
    """
    problem_idの問題に類似度の高い問題をN返す。
    difficultyを渡すと難易度を考慮して返す。(毎度difficultyを取得すると時間がかかるので引数で渡す。)
    (problem_id, score)[]
    """
    problems_json = get_json("data/problems_editorial.json")
    problems_json = {k: v for k, v in problems_json.items() if not v is None}

    # IDの解説が存在しない場合空リストを返す
    if not problem_id in problems_json:
        return []
    target = problems_json[problem_id]
    del problems_json[problem_id]
    
    # テキストの前処理
    def preprocess_text(text):
        text = re.sub(r'\n', ' ', text).strip()
        return text

    processed_corpus = [preprocess_text(p["text"]) for p in problems_json.values()]
    processed_target = preprocess_text(target["text"])

    vectorizer = TfidfVectorizer()
    tfidf_matrix_corpus = vectorizer.fit_transform(processed_corpus)
    tfidf_vector_target = vectorizer.transform([processed_target])

    similarities = cosine_similarity(tfidf_matrix_corpus, tfidf_vector_target)

    # for i, score in enumerate(similarities):
    #     print(f"{list(problems_json.keys())[i]} score: {score[0]:.4f}")

    def calc_score(target_id, score):
        """
        難易度を考慮してスコアを計算する
        """
        try :
            problem_diff = difficulty[problem_id]["difficulty"]
            target_diff = difficulty[target_id]["difficulty"]
            if problem_diff is None or target_diff is None :
                return -1000
            
            orrection = 200 if least_diff < 0 else 0
            # print(f"problemID: {problem_id}, targetID: {target_id} diff: {abs(problem_diff - target_diff)} score: {score - (abs(problem_diff - target_diff) / 3000)}")
            return score - (abs((problem_diff - orrection) - target_diff) / 3000)
        except:
            return score

    scores = [(list(problems_json.keys())[i], s[0]) for i, s in enumerate(similarities)]
    scores = sorted(scores, key=lambda x: calc_score(x[0], x[1]), reverse=True)
    return scores[:N]

def get_recomend_problem(user, histories=None):
    """
    不正解だった問題を元におすすめの問題のリストを返す  
    return (id, score)[][]
    """
    submissions_list = get_submissions_merge_contest_info(user, histories=histories)
    problems = set()
    for submissions in submissions_list.values():
        for submission in submissions:
            result = submission["result"]
            if result == "WA" or result == "TLE":
                problems.add(submission["problem_id"])

    difficulty = get_difficulties()
    if histories is None:
        least_diff = 0
    else:
        least_diff = histories[0]["diff"]
    return [get_similarity_problems(p, difficulty=difficulty, least_diff=least_diff) for p in problems]


def run():
    windowShow()

    # user = "kiiiiiii"
    # histories = get_histories(user)
    # least_diff = histories[0]["diff"]

    # difficulties = get_difficulties()

    # use_gemini("""リンゴの魅力について簡潔に教えてください。""", TEST=True)


if __name__ == "__main__":
    if TEST:
        print("テストモードで実行しています。")


    run()

    # user = "kiiiiiii"
    # histories = get_histories()
    # recomend = get_recomend_problem(user, histories=histories)
    
    
    # recomends = get_recomend_problem("kiiiiiii")
    # for problems in recomends:
    #     for problem in problems:
    #         print(problem)

    # result = get_submissions_merge_contest_info("kiiiiiii")
    # for id, submissions in result.items():
    #     print(id)
    #     for submission in submissions:
    #         sim_problem = get_similarity_problems(submission["problem_id"])[0][0]
    #         print(f"    {submission['epoch_second']}: {submission['problem_id']} - {submission['result']} ({submission['language']}) simproblem: {sim_problem}")
    # print(get_similarity_problems("abc300_a", difficulty=get_difficulties()))