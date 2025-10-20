import tkinter as tk

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

        # --- インスタンス変数として状態を管理 ---
        self.pos = 0
        self.amp = [0] * 32

        # --- 定数 ---
        self.CANVAS_WIDTH = 642
        self.CANVAS_HEIGHT = 342
        self.GRID_SPACING = 20

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

        # ボタン
        button_u = tk.Button(button_frame, text="Up (U)", command=self.click_button_u)
        button_u.grid(row=0, column=1, padx=5)
        button_l = tk.Button(button_frame, text="Left (L)", command=self.click_button_l)
        button_l.grid(row=1, column=0, padx=5)
        button_d = tk.Button(button_frame, text="Down (D)", command=self.click_button_d)
        button_d.grid(row=1, column=1, padx=5)
        button_r = tk.Button(button_frame, text="Right (R)", command=self.click_button_r)
        button_r.grid(row=1, column=2, padx=5)

        # --- 初期描画 ---
        self.draw_grid()
        self.draw_amplitudes()
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

        # 中央線
        center_y = self.CANVAS_HEIGHT / 2
        self.canvas.create_line(0, center_y, self.CANVAS_WIDTH, center_y, fill="red", dash=(4, 2))

    def draw_amplitudes(self):
        """
        amp配列に基づいてすべての振幅バーを描画します。
        """
        self.canvas.delete("amplitudes") # 既存のバーをすべて削除
        center_y = self.CANVAS_HEIGHT / 2
        
        for i, val in enumerate(self.amp):
            x0 = self.GRID_SPACING * i
            y0 = center_y - self.GRID_SPACING * val
            x1 = self.GRID_SPACING * (i + 1)
            y1 = center_y
            
            # 振幅が正か負かで開始点を調整
            if val < 0:
                y0, y1 = y1, y0
            
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
        if self.amp[self.pos] < 8:
            self.amp[self.pos] += 1
            self.draw_amplitudes()
        else:
            print("これより振幅を上げられません")
        print(f"pos = {self.pos}, amp[{self.pos}] = {self.amp[self.pos]}")

    def click_button_d(self):
        """
        'Down'ボタンがクリックされたときの処理。振幅を下げます。
        """
        if self.amp[self.pos] > -8:
            self.amp[self.pos] -= 1
            self.draw_amplitudes()
        else:
            print("これより振幅を下げられません")
        print(f"pos = {self.pos}, amp[{self.pos}] = {self.amp[self.pos]}")

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
        if self.pos < 31:
            self.pos += 1
            self.draw_pointer()
        else:
            print("これより右に移動できません")
        print(f"pos = {self.pos}")


if __name__ == "__main__":
    # ウィンドウの作成とアプリケーションの実行
    root = tk.Tk()
    app = AmplitudeEditorApp(root)
    root.mainloop()

