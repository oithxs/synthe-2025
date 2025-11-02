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

        # ファイル名表示ラベル
        file_info_label = tk.Label(self.master, text="現在の波形ファイル:", font=('', 12))
        file_info_label.pack(pady=6)
        # 表示用 StringVar と実ファイルパスを分離
        self.file_name_var = tk.StringVar(value='未選択です')
        self.file_path = None
        self.selected_wav = ''
        file_name_label = tk.Label(textvariable=self.selected_wav, font=('', 12))
        file_name_label.pack(pady=6)

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
        music_files = sorted(os.listdir(self.get_curdir() + "/mmls"))
        print(f"利用可能な音楽ファイル: {music_files}")
        # 拡張子を消してlistに入れる
        music_options = []
        for f in music_files:
            if f.endswith('.mml'):
                music_options.append(f[:-4])
        # music_options = ['Bad-Apple!!', 'Mario_Theme', 'Mario_Star', 'Old_KCS_Song', 'idol']
        for option in music_options:
            self.music_listbox.insert(tk.END, option)
        self.music_listbox.grid(row=0, column=3, padx=5)
        self.music_listbox.select_set(0)  # デフォルトで最初の曲を選択
        # 矢印キーのイベントバインドを上書き
        # <Up> と <Down> キーのデフォルト動作を無効化
        # bind に関数参照を渡す（() を付けると即時実行される）
        self.music_listbox.bind('<Up>', self.disable_arrow_keys)
        self.music_listbox.bind('<Down>', self.disable_arrow_keys)

        # Playボタン
        button_play = tk.Button(button_frame, text='Play', font=('', 10),
                           width=18, height=1, bg='#999999', activebackground="#aaaaaa")
        button_play.bind('<ButtonPress>', self.click_button_play)
        button_play.grid(row=1, column=3, padx=5)

        # 波形ファイル選択リストボックス
        self.wavetable_listbox = tk.Listbox(button_frame, height=4, exportselection=False)
        wt_files = sorted(os.listdir(self.get_curdir() + "/wavetables"))
        print(f"利用可能な波形ファイル: {wt_files}")
        # 拡張子を消してlistに入れる
        wavetable_options = []
        for f in wt_files:
            if f.endswith('.txt'):
                wavetable_options.append(f[:-4])
        #wavetable_options = ['sine1', 'square1', 'sawtooth', 'triangle', 'pulse']
        for option in wavetable_options:
            self.wavetable_listbox.insert(tk.END, option)
        self.wavetable_listbox.grid(row=0, column=4, padx=5)
        self.wavetable_listbox.select_set(0)  # デフォルトで最初のファイルを選択
        self.wavetable_listbox.bind('<<ListboxSelect>>', self.load_preset)
        # 矢印キーのイベントバインドを上書き
        # <Up> と <Down> キーのデフォルト動作を無効化
        self.wavetable_listbox.bind('<Up>', self.disable_arrow_keys)
        self.wavetable_listbox.bind('<Down>', self.disable_arrow_keys)

        # 波形ファイルの読み込み・保存ボタン
        #button_fileopen = tk.Button(button_frame, text='波形ファイルを開く', font=('', 10),
        #                   width=18, height=1, bg='#999999', activebackground="#aaaaaa")
        #button_fileopen.bind('<ButtonPress>', self.file_open_dialog)
        #button_fileopen.grid(row=2, column=4, padx=5)
        
        # 波形ファイルリストの更新ボタン
        button_refresh = tk.Button(button_frame, text='波形ファイルリストを更新', font=('', 10),
                           width=22, height=1, bg='#999999', activebackground="#aaaaaa")
        button_refresh.bind('<ButtonPress>', self.refresh_wavetable_list)
        button_refresh.grid(row=1, column=4, padx=5)

        # 波形ファイルの保存ボタン
        button_filewrite = tk.Button(button_frame, text='波形ファイルを書き込み', font=('', 10),
                           width=22, height=1, bg='#999999', activebackground="#aaaaaa")
        button_filewrite.bind('<ButtonPress>', self.file_save_dialog)
        button_filewrite.grid(row=2, column=4, padx=5)

        # キーボード入力を受け付ける（U/D/L/R と矢印に対応）
        # bind_all にしておくと listbox にフォーカスがあっても on_key が呼ばれる
        self.master.bind_all('<Key>', self.on_key)
        # フォーカスがないとキーイベントが来ないのでフォーカスを設定
        self.master.focus_set()

        # --- 初期描画 ---
        self.draw_grid()
        self.draw_amplitudes()
        self.draw_center_line()
        self.draw_pointer()
        self.load_preset()
    
    def disable_arrow_keys(self, event):
        # listbox上での上下矢印のデフォルト選択移動を抑止し、
        # アプリ共通のキー処理を実行する（振幅操作を有効にする）
        self.on_key(event)
        return "break"

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
        #print(f"pos = {self.pos}")

    def click_button_r(self):
        """
        'Right'ボタンがクリックされたときの処理。位置を右に移動します。
        """
        if self.pos < self.WAVE_LENGTH-1:
            self.pos += 1
            self.draw_pointer()
        else:
            print("これより右に移動できません")
        #print(f"pos = {self.pos}")
    
    def get_selected_wav(self):
        selected_index = self.wavetable_listbox.curselection()
        if not selected_index:
            return None
        return self.wavetable_listbox.get(selected_index)
    
    def get_selected_music(self):
        selected_index = self.music_listbox.curselection()
        if not selected_index:
            return None
        return self.music_listbox.get(selected_index)
    
    def get_curdir(self):
        return os.path.abspath(os.path.dirname(__file__))
    
    def click_button_play(self,event=None):
        """
        'play'ボタンがクリックされたときの処理。音楽を再生する。
        """
        
        self.selected_wav = self.get_selected_wav()
        print(f"選択された波形ファイル: {self.selected_wav}")
        selected_song = self.get_selected_music()
        print(f"選択された曲: {selected_song}")
        
        # ここで選択された曲に基づいて再生処理を実行する
        wav_path = f"./wavetables/{self.selected_wav}.txt"
        mml_path = f"./mmls/{selected_song}.mml"
        cmd = f'gcc -o hoge sound_test.c mml_parser.c -lm -lasound && ./hoge "{wav_path}" "{mml_path}" &'
        os.system(cmd)
        
    def load_preset(self, event=None):
        """
        wav_path が指すファイルから振幅データを読み込む。
        ファイル内の最初の非空行を読み、スペース区切りの整数列として self.amp を更新する。
        要素数が足りない場合は残りを 0 で埋める。範囲は AMP_MIN/AMP_MAX にクランプ。
        """
        self.selected_wav = self.get_selected_wav()
        wav_path = os.path.abspath(os.path.dirname(__file__)) + f"/wavetables/{self.selected_wav}.txt"
        print(f"load_preset: 読み込み元 = {wav_path}")
        if not wav_path:
            print("load_preset: ファイルが指定されていません")
            return
        try:
            with open(wav_path, "r", encoding="utf-8") as infile:
                for line in infile:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split()
                    vals = []
                    for p in parts:
                        try:
                            v = int(float(p))
                        except ValueError:
                            v = 0
                        # clamp
                        if v > self.AMP_MAX:
                            v = self.AMP_MAX
                        if v < self.AMP_MIN:
                            v = self.AMP_MIN
                        vals.append(v)
                    # fill or trim to WAVE_LENGTH
                    if len(vals) < self.WAVE_LENGTH:
                        vals.extend([0] * (self.WAVE_LENGTH - len(vals)))
                    else:
                        vals = vals[:self.WAVE_LENGTH]
                    self.amp = vals
                    break
            self.draw_amplitudes()
            # ensure pointer in range
            if self.pos >= len(self.amp):
                self.pos = 0
            self.draw_pointer()
        except Exception as e:
            print(f"load_preset: 読み込みエラー: {e}")
        
    
    def file_open_dialog(self, event):
        fTyp = [("", ".txt")]
        iDir = os.path.abspath(os.path.dirname(__file__))  + "/wavetables"
        print(f"初期ディレクトリ: {iDir}")
        path = tk.filedialog.askopenfilename(filetypes=fTyp, initialdir=iDir)
        if not path:
            self.file_name_var.set('選択をキャンセルしました')
            self.file_path = None
            return
        self.file_path = path
        self.file_name_var.set(os.path.basename(path))
        self.load_preset()

    def save_wave(self):
        """
        現在の self.file_path に振幅データを書き込む。
        """
        print(f"save_wave: 保存先 = {self.file_path}")
        if not self.file_path:
            print("save_wave: 保存先が指定されていません")
            return
        try:
            with open(self.file_path, "w", encoding="utf-8") as outfile:
                outfile.write(" ".join(str(int(v)) for v in self.amp))
            print(f"保存しました: {self.file_path}")
        except Exception as e:
            print(f"save_wave: 保存エラー: {e}")
        
    
    def file_save_dialog(self, event):
        fTyp = [("", ".txt")]
        iDir = "./wavetables"
        path = tk.filedialog.asksaveasfilename(filetypes=fTyp, initialdir=iDir)
        if not path:
            return
        self.file_path = path
        self.file_name_var.set(os.path.basename(path))
        self.save_wave()
    
    def on_key(self, event):
        """
        キーイベントハンドラ。letters (u/d/l/r) と矢印キーを処理して既存のボタン処理を呼ぶ。
        """
        k = (event.keysym or "").lower()
        #print(f"on_key: 押されたキー = {k}")
        if k in ('u', 'up'):
            self.click_button_u()
        elif k in ('d', 'down'):
            self.click_button_d()
        elif k in ('l', 'left'):
            self.click_button_l()
        elif k in ('r', 'right'):
            self.click_button_r()
    
    def refresh_wavetable_list(self, event):
        self.wavetable_listbox.delete(0, tk.END)
        wt_files = sorted(os.listdir(self.get_curdir() + "/wavetables"))
        print(f"利用可能な波形ファイル: {wt_files}")
        # 拡張子を消してlistに入れる
        wavetable_options = []
        for f in wt_files:
            if f.endswith('.txt'):
                wavetable_options.append(f[:-4])
        for option in wavetable_options:
            self.wavetable_listbox.insert(tk.END, option)

if __name__ == "__main__":
    # ウィンドウの作成とアプリケーションの実行
    root = tk.Tk()
    app = AmplitudeEditorApp(root)
    root.mainloop()

