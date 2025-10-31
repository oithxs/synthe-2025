import os
import tkinter as tk
import tkinter.filedialog
from tkinter import ttk

class AmplitudeEditorApp:
    """
    Tkinterを使用して振幅を編集・表示するアプリケーションクラス。
    """
    def __init__(self, master):
        """
        アプリケーションを初期化し、UIウィジェットを作成します。
        """
        self.master = master
        self.master.title("振幅エディタ")

        # --- 定数 ---
        self.WAVE_LENGTH = 32 # 波長

        # --- 定数-振幅の上限/下限 ---
        self.AMP_MAX = 7
        self.AMP_MIN = -8

        # --- 定数-キャンバス関係 ---
        self.CANVAS_WIDTH = 642
        self.CANVAS_HEIGHT = 342
        self.GRID_SPACING = 20
        self.CENTER_Y = (self.CANVAS_HEIGHT / 2) - self.GRID_SPACING

        # --- インスタンス変数として状態を管理 ---
        self.pos = 0
        self.amp = [0] * self.WAVE_LENGTH

        # --- UIウィジェットの作成 ---
        # 説明ラベル
        info_label = tk.Label(self.master, text="U/Dキーで振幅、L/Rキーで位置を操作します", font=("Helvetica", 12))
        info_label.pack(pady=5)

        # キャンバス
        self.canvas = tk.Canvas(self.master, width=self.CANVAS_WIDTH, height=self.CANVAS_HEIGHT, bg="white")
        self.canvas.pack(pady=10, padx=10)

        # ボタンを格納するフレーム
        button_frame = tk.Frame(self.master)
        button_frame.pack(pady=5)

        # 波形編集ボタン
        button_u = tk.Button(button_frame, text="Up (U)", command=self.click_button_u)
        button_u.grid(row=0, column=1, padx=5)
        button_l = tk.Button(button_frame, text="Left (L)", command=self.click_button_l)
        button_l.grid(row=1, column=0, padx=5)
        button_d = tk.Button(button_frame, text="Down (D)", command=self.click_button_d)
        button_d.grid(row=1, column=1, padx=5)
        button_r = tk.Button(button_frame, text="Right (R)", command=self.click_button_r)
        button_r.grid(row=1, column=2, padx=5)

        # 音楽選択リストボックス
        self.music_listbox = tk.Listbox(button_frame, height=4, exportselection=False)
        music_options = ['Bad-Apple!!', 'Mario_Theme', 'Old_KCSSong']
        for option in music_options:
            self.music_listbox.insert(tk.END, option)
        self.music_listbox.grid(row=0, column=3, padx=5)
        self.music_listbox.select_set(0)  # デフォルトで最初の曲を選択
        #self.music_listbox.bind('<<ListboxSelect>>', self.on_music_select)

        # Playボタン
        button_play = tk.Button(button_frame, text='Play', font=('', 10),
                           width=18, height=1, bg='#999999', activebackground="#aaaaaa")
        button_play.bind('<ButtonPress>', self.click_button_play)
        button_play.grid(row=1, column=3, padx=5)

        # 波形ファイルの読み込み・保存ボタン
        button_fileopen = tk.Button(button_frame, text='波形ファイルを開く', font=('', 10),
                           width=18, height=1, bg='#999999', activebackground="#aaaaaa")
        button_fileopen.bind('<ButtonPress>', self.file_open_dialog)
        button_fileopen.grid(row=0, column=4, padx=5)

        self.file_name = ""#tk.StringVar()
        #self.file_name.set('未選択です')
        #label = tk.Label(textvariable=self.file_name, font=('', 12))
        #label.pack(pady=0)

        button_filewrite = tk.Button(button_frame, text='波形ファイルを書き込み', font=('', 10),
                           width=22, height=1, bg='#999999', activebackground="#aaaaaa")
        button_filewrite.bind('<ButtonPress>', self.file_save_dialog)
        button_filewrite.grid(row=1, column=4, padx=5)

        # キーボード入力を受け付ける（U/D/L/R と矢印に対応）
        self.master.bind('<Key>', self.on_key)
        # フォーカスがないとキーイベントが来ないのでフォーカスを設定
        self.master.focus_set()

        # --- 初期描画 ---
        self.draw_grid()
        self.draw_amplitudes()
        self.draw_center_line()
        self.draw_pointer()

    def draw_grid(self):
        """
        キャンバスにグリッドを描画します。
        """
        # 縦線
        for i in range(self.GRID_SPACING, self.CANVAS_WIDTH, self.GRID_SPACING):
            self.canvas.create_line(i, 0, i, self.CANVAS_HEIGHT, fill="#e0e0e0")
        
        # 横線
        for i in range(self.GRID_SPACING, self.CANVAS_HEIGHT, self.GRID_SPACING):
            self.canvas.create_line(0, i, self.CANVAS_WIDTH, i, fill="#e0e0e0")

    def draw_center_line(self):
        # 中央線
        self.canvas.create_line(0, self.CENTER_Y, self.CANVAS_WIDTH, self.CENTER_Y, fill="red", dash=(4, 2))


    def draw_amplitudes(self):
        """
        amp配列に基づいてすべての振幅バーを描画します。
        """
        self.canvas.delete("amplitudes") # 既存のバーをすべて削除
        
        for i, val in enumerate(self.amp):
            near_cemter_y = self.CENTER_Y
            if (val < 0):
                near_cemter_y += 2
            else:
                near_cemter_y -= 2
            
            x0 = self.GRID_SPACING * i
            y0 = near_cemter_y - self.GRID_SPACING * val
            x1 = self.GRID_SPACING * (i + 1)
            y1 = near_cemter_y
            
            # 振幅が正か負かで開始点を調整
            if val < 0:
                y0, y1 = y1, y0
            
            #print(f"x0 = {x0}, y0 = {y0}, x1 = {x1}, y1 = {y1}")
            
            self.canvas.create_rectangle(x0, y0, x1, y1, fill="blue", tag="amplitudes", outline="white")

    def draw_pointer(self):
        """
        現在の位置(pos)を示すポインタを描画します。
        """
        self.canvas.delete("pointer")
        x = self.GRID_SPACING * self.pos + (self.GRID_SPACING / 2)
        y = self.CANVAS_HEIGHT - 10
        self.canvas.create_text(x, y, text="^", font=("Helvetica", 16), fill="green", tag="pointer")

    def click_button_u(self):
        """
        'Up'ボタンがクリックされたときの処理。振幅を上げます。
        """
        if self.amp[self.pos] < self.AMP_MAX:
            self.amp[self.pos] += 1
            self.draw_amplitudes()
        else:
            print("click_button_u: これより振幅を上げられません")
        #print(f"pos = {self.pos}, amp[{self.pos}] = {self.amp[self.pos]}")

    def click_button_d(self):
        """
        'Down'ボタンがクリックされたときの処理。振幅を下げます。
        """
        if self.amp[self.pos] > self.AMP_MIN:
            self.amp[self.pos] -= 1
            self.draw_amplitudes()
        else:
            print("click_button_d: これより振幅を下げられません")
        #print(f"pos = {self.pos}, amp[{self.pos}] = {self.amp[self.pos]}")

    def click_button_l(self):
        """
        'Left'ボタンがクリックされたときの処理。位置を左に移動します。
        """
        if self.pos > 0:
            self.pos -= 1
            self.draw_pointer()
        else:
            print("これより左に移動できません")
        print(f"pos = {self.pos}")

    def click_button_r(self):
        """
        'Right'ボタンがクリックされたときの処理。位置を右に移動します。
        """
        if self.pos < self.WAVE_LENGTH-1:
            self.pos += 1
            self.draw_pointer()
        else:
            print("これより右に移動できません")
        print(f"pos = {self.pos}")
    
    def click_button_play(self,event=None):
        """
        'play'ボタンがクリックされたときの処理。音楽を再生する。
        """
        selected_index = self.music_listbox.curselection()
        if not selected_index:
            print("曲が選択されていません")
            return
        selected_song = self.music_listbox.get(selected_index)
        print(f"選択された曲: {selected_song}")
        # ここで選択された曲に基づいて再生処理を実行します
        # 例:
        os.system(f'gcc -o hoge sound_test.c mml_parser.c -lm -lasound && ./hoge {selected_song}.mml &')

    
    def load_preset(self):
        with open(self.file_name, "r", encoding="utf-8") as infile:
            for line in infile:
                self.amp = [float(x) for x in line.split()]
            
            self.draw_amplitudes()
            for i in self.amp:
                print(f"lp: i={i}")
        
    
    def file_open_dialog(self, event):
        fTyp = [("", "*")]
        iDir = os.path.abspath(os.path.dirname(__file__))
        self.file_name = tk.filedialog.askopenfilename(filetypes=fTyp, initialdir=iDir)
        #if len(file_name) == 0:
        #    self.file_name.set('選択をキャンセルしました')
        #else:
        #    self.file_name.set(file_name)
        self.load_preset()

    def save_wave(self):
        with open(self.file_name, "w", encoding="utf-8") as infile:
            for i in self.amp:
                infile.write(f"{i} ")
        
    
    def file_save_dialog(self, event):
        fTyp = [("", "*")]
        iDir = os.path.abspath(os.path.dirname(__file__))
        self.file_name = tk.filedialog.asksaveasfilename(filetypes=fTyp, initialdir=iDir)
        print(f"saving to {self.file_name}")
        self.save_wave()
    
    def on_key(self, event):
        """
        キーイベントハンドラ。letters (u/d/l/r) と矢印キーを処理して既存のボタン処理を呼ぶ。
        """
        k = (event.keysym or "").lower()
        if k in ('u', 'up'):
            self.click_button_u()
        elif k in ('d', 'down'):
            self.click_button_d()
        elif k in ('l', 'left'):
            self.click_button_l()
        elif k in ('r', 'right'):
            self.click_button_r()

if __name__ == "__main__":
    # ウィンドウの作成とアプリケーションの実行
    root = tk.Tk()
    app = AmplitudeEditorApp(root)
    root.mainloop()

