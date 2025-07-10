import random
import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QLineEdit, QTextEdit, QPushButton, QRadioButton, QLabel, QFrame
from PyQt6.QtGui import QDesktopServices, QCursor
from PyQt6.QtCore import Qt, QUrl, pyqtSignal
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
from main import get_histories, get_gemini_advice, get_recomend_problem, get_detailed_problems_information, get_difficulties

FONT_PATH = "C:/Windows/Fonts/BIZ-UDGOTHICR.TTC"
font_prop = FontProperties(fname=FONT_PATH)

plt.rcParams["font.family"] = font_prop.get_name()
plt.rcParams["axes.unicode_minus"] = False

USER_COLORS = {
    "gray": "#808080", 
    "brown": "#804000", 
    "green": "#008000", 
    "cyan": "#00c0c0", 
    "blue": "#0000ff", 
    "yellow": "#c0c000", 
    "orange": "#ff8000", 
    "red": "#ff0000"
}

COLOR_BORDERS = (
    ("gray", 400),
    ("brown", 800),
    ("green", 1200),
    ("cyan", 1600),
    ("blue", 2000),
    ("yellow", 2400),
    ("orange", 2800),
    ("red", -1)
)

def get_diff_color(diff) :
    diff = max(diff, 0)
    for border in COLOR_BORDERS:
        if diff < border[1]:
            return USER_COLORS[border[0]]
    return USER_COLORS["red"]

class ATCProWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initGUI()

    def initGUI(self):
        self.setWindowTitle("atcpro")
        self.setGeometry(100, 100, 1000, 750)

        self.setStyleSheet("""
            ATCProWindow {
            }
            ATCProWindow QLabel[class='title']{
                font-size: 20px;
                font-weight: bold;
            }
            ATCProWindow #aiText {
                background-color: #e0e0e0;
                border: solid 1px #c0c0c0;
                border-radius: 10px;
                padding: 10px;
            }
        """)

        layout = QVBoxLayout()

        # - row1: 検索
        row1 = QHBoxLayout()

        # -- 検索ボックス
        self.user_input = QLineEdit(self)
        self.user_input.setPlaceholderText("例) kiiiiiii")
        self.user_input.setText("kiiiiiii")
        self.user_input.setToolTip("ユーザー名")
        
        # -- 検索ボタン
        self.search_button = QPushButton("検索", self)
        self.search_button.clicked.connect(self.on_search_click)

        row1.addWidget(self.user_input, 1)
        row1.addWidget(self.search_button, 0)


        # - row2: ヒストリーとAI
        row2 = QHBoxLayout()

        # -- グラフ
        # self.history_graph = self.update_history_graph()
        self.history_fig = Figure()
        self.history_ax = self.history_fig.add_subplot(111)
        self.history_graph = FigureCanvas(self.history_fig)
        self.update_history_graph()
        
        # -- AIコンテンツ
        ai_layout = QVBoxLayout()
        
        # --- AIタイプラジオボタン
        ai_type_button_layout = QHBoxLayout()
        ai_types = ("祖母", "祖父", "母", "父", "姉", "兄", "妹", "弟")
        self.ai_type_buttons = [QRadioButton(ai_type, self) for ai_type in ai_types ]
        self.ai_type_buttons[0].setChecked(True)
        for ai_type_button in self.ai_type_buttons:
            ai_type_button.clicked.connect(self.on_change_ai_type)
            ai_type_button_layout.addWidget(ai_type_button)

        # --- AIテキスト
        ai_text_layout = QVBoxLayout()
        self.ai_text_title = QLabel()
        self.ai_text_title.setProperty("class", "title")
        self.on_change_ai_type()
        self.ai_text = QLabel("...")
        self.ai_text.setWordWrap(True)
        self.ai_text.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.ai_text.setObjectName("aiText")
        ai_text_layout.addWidget(self.ai_text_title, 0)
        ai_text_layout.addWidget(self.ai_text, 1)

        ai_layout.addLayout(ai_type_button_layout)
        ai_layout.addLayout(ai_text_layout)

        row2.addWidget(self.history_graph, 2)
        row2.addLayout(ai_layout, 3)

        # - row3: おすすめ問題
        row3 = QVBoxLayout()

        # -- おすすめ問題タイトル
        recomend_title = QLabel("おすすめ問題")
        recomend_title.setProperty("class", "title")

        # -- おすすめ問題リンク
        links_scroll_area = QScrollArea()
        links_scroll_area.setWidgetResizable(True)
        links_content = QWidget()
        self.links_scroll_layout = QHBoxLayout(links_content)
        self.update_recomend_card()
        # for data in link_data:
        #     card = LinkCard(data["title"], data["description"], data["url"])
        #     card.clicked.connect(self.open_url_in_browser)
        #     self.links_scroll_layout.addWidget(card, 1)
        links_scroll_area.setWidget(links_content)

        row3.addWidget(recomend_title)
        row3.addWidget(links_scroll_area)


        layout.addLayout(row1, 0)
        layout.addLayout(row2, 1)
        layout.addLayout(row3, 0)


        self.setLayout(layout)

        

    def on_search_click(self):
        """
        検索ボタンを押したときの処理
        """
        user = self.user_input.text()
        histories = get_histories(user)
        self.update_history_graph(histories=histories)
        recomends, difficulty = get_recomend_problem(user, histories=histories)
        ai_text = get_gemini_advice(user, self.get_ai_type(), histories=histories, recomend_problems=recomends, TEST=True)
        if ai_text is None:
            self.ai_text.setText("取得できませんでした！ごめんなさい！")
        else:
            self.ai_text.setText(ai_text)
            print(ai_text)
        self.update_recomend_card(recomends=recomends, difficulty=difficulty)

    def on_change_ai_type(self):
        """
        ai_typeを変えた時の処理
        """
        self.ai_text_title.setText(f"{self.get_ai_type()}のアドバイス")

    def get_ai_type(self):
        """
        ai_typeの文字列を取得する
        """
        for ai_type_button in self.ai_type_buttons:
            if ai_type_button.isChecked():
                return ai_type_button.text()
        return ""
    
    def update_history_graph(self, histories=None):
        self.history_ax.clear()

        self.history_ax.axhspan(0, 400, facecolor=USER_COLORS["gray"], alpha=0.3)
        self.history_ax.axhspan(400, 800, facecolor=USER_COLORS["brown"], alpha=0.3)
        self.history_ax.axhspan(800, 1200, facecolor=USER_COLORS["green"], alpha=0.3)
        self.history_ax.axhspan(1200, 1600, facecolor=USER_COLORS["cyan"], alpha=0.3)
        self.history_ax.axhspan(1600, 2000, facecolor=USER_COLORS["blue"], alpha=0.3)
        self.history_ax.axhspan(2000, 2400, facecolor=USER_COLORS["yellow"], alpha=0.3)
        self.history_ax.axhspan(2400, 2800, facecolor=USER_COLORS["orange"], alpha=0.3)
        self.history_ax.axhspan(2800, 4000, facecolor=USER_COLORS["red"], alpha=0.3)

        if not histories is None:
            histories.reverse()
            x = [history["contest_id"] for history in histories]
            y = [history["rating"] for history in histories]
            self.history_fig.autofmt_xdate()
        else:
            x = [p for p in range(10)]
            y = [(p + 1) * 50 + random.randint(-50, 50) for p in range(10)]
        if y:
            remove_set = {i for i, v in enumerate(y) if type(v) != int}
            y = [v for i, v in enumerate(y) if not i in remove_set]
            x = [v for i, v in enumerate(x) if not i in remove_set]
            if len(y) > 0:
                min_y = max(0, min(y) - 50)
                max_y = max(y) + 50
                self.history_ax.set_ylim(min_y, max_y)
                point_colors = [get_diff_color(rating) for rating in y]
                self.history_ax.plot(x, y, linestyle="-", color="darkgray", zorder=3)
                self.history_ax.scatter(x, y, c=point_colors, zorder=4, edgecolors="black", linewidths=0.5)

        # self.history_ax.plot(x, y, marker="o", linestyle="-", color="gray" if histories is None else "blue")        
        self.history_ax.set_title(f"レート推移{'(サンプル)' if histories is None else ''}")
        self.history_ax.set_xlabel("コンテスト")
        self.history_ax.set_ylabel("レート")
        self.history_ax.grid(True)

        self.history_fig.tight_layout()
        self.history_graph.draw()
    
    def update_recomend_card(self, recomends=None, difficulty=None):
        if recomends is None:
            card = LinkCard(title="Sample", name="sample", diff=0, url="")
            self.links_scroll_layout.addWidget(card)
            return 

        while self.links_scroll_layout.count():
            child = self.links_scroll_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if difficulty is None:
            difficulty = get_difficulties()
        problems_detail = get_detailed_problems_information()
        problems_detail = {p["id"]: p for p in problems_detail}
        problems = [problems_detail[r[0]] for r in recomends if r[0] in problems_detail]
        
        for problem in problems:
            problem_id = problem["id"]
            if not problem_id in difficulty:
                diff = 0
            else :
                diff = difficulty[problem_id]["difficulty"]
            if not problem_id in problems_detail:
                url = ""
            else :
                detail = problems_detail[problem_id]
                if not "contest_id" in detail:
                    url = ""
                else :
                    url = f"https://atcoder.jp/contests/{detail['contest_id']}/tasks/{problem_id}"
            
            card = LinkCard(problem_id, problem['name'], diff, url)
            card.clicked.connect(self.open_url_in_browser)
            self.links_scroll_layout.addWidget(card, 1)

    def open_url_in_browser(self, url):
        QDesktopServices.openUrl(QUrl(url))


class LinkCard(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, title, name, diff, url ,parent=None):
        super().__init__(parent)
        self.url = url

        diff_color = get_diff_color(diff)

        self.setStyleSheet(f"""
            LinkCard {{
                background-color: #f0f0f0; /* 薄いグレーの背景 */
                border: 1px solid #c0c0c0; /* 薄いボーダー */
                border-radius: 8px; /* 角丸 */
                padding: 2px; /* 内側の余白 */
                margin-bottom: 20px; /* カード間の下マージン */
            }}
            LinkCard:hover {{
                background-color: #e0e0e0; /* ホバー時の色変更 */
            }}
            LinkCard QLabel#titleLabel {{ /* タイトルラベルのスタイル */
                font-size: 16px;
                font-weight: bold;
                color: {diff_color};
            }}
            LinkCard QLabel#descriptionLabel {{ /* 説明ラベルのスタイル */
                font-size: 12px;
                color: #666666;
            }}
        """)

        card_layout = QVBoxLayout()

        self.title_label = QLabel(title)
        self.title_label.setObjectName("titleLabel")
        self.title_label.setWordWrap(True)

        self.description_label = QLabel(f"{name}\ndiff:{diff}")
        self.description_label.setObjectName("descriptionLabel")
        # self.description_label.setWordWrap(True)

        card_layout.addWidget(self.title_label)
        card_layout.addWidget(self.description_label)
        card_layout.addStretch(1)

        self.setLayout(card_layout)

    def mousePressEvent(self, event):
        self.clicked.emit(self.url)
        super().mousePressEvent(event)


def windowShow():
    qAp = QApplication(sys.argv)
    atcw = ATCProWindow()
    atcw.show()
    qAp.exec()

if __name__ == "__main__":
    windowShow()