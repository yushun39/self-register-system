import tkinter as tk
from tkinter import ttk
from tkinterdnd2 import DND_FILES, TkinterDnD
from tkinter import messagebox

from PIL import Image
from pyzbar.pyzbar import decode

import requests
from bs4 import BeautifulSoup
import winsound

from PIL import ImageTk
import io

class Application(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()

        self.title("簡易レジ")
        self.geometry("550x900")
        self.resizable(False, False)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=0)
        self.rowconfigure(3, weight=1)
        self.rowconfigure(4, weight=1)

        frame_1 = tk.Frame(self)
        frame_1.columnconfigure(0, weight=1)
        frame_1.rowconfigure(1, weight=1)
        frame_1.grid(row=0, column=0, sticky="nsew")
        self.scan_label = tk.Label(frame_1, text="スキャン履歴", font=("Meiryo", 16, "bold"), relief="ridge", anchor="center")
        self.scan_label.grid(row=0, column=0, padx=5, pady=5)
        self.listbox = tk.Listbox(frame_1)
        self.listbox.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        separator = ttk.Separator(self, orient="horizontal")
        separator.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        
        frame_2 = tk.Frame(self, height=300)
        frame_2.rowconfigure(0, weight=1)
        frame_2.columnconfigure(0, weight=1)
        frame_2.columnconfigure(1, weight=1)
        frame_2.grid(row=2, column=0, sticky="nsew")
        frame_2.grid_propagate(False)
        self.image = tk.Label(frame_2, text="画像表示", image='')
        self.image.grid(row=0, column=0, columnspan=2)
        self.name = tk.Label(frame_2, text="商品名：", font=("Meiryo", 16, "bold"), relief="ridge", anchor="center")
        self.name.grid(row=1, column=0, columnspan=2, padx=5)
        self.price = tk.Label(frame_2, text="価格：", relief="ridge")
        self.price.grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.JAN = tk.Label(frame_2, text="JAN：", relief="ridge")
        self.JAN.grid(row=2, column=1, sticky="w", padx=5, pady=5)

        separator = ttk.Separator(self, orient="horizontal")
        separator.grid(row=3, column=0, padx=10, pady=5, sticky="ew")

        frame_3 = tk.Frame(self)
        frame_3.rowconfigure(0, weight=2)
        frame_3.rowconfigure(1, weight=0)
        frame_3.columnconfigure(0, weight=1)
        frame_3.columnconfigure(1, weight=1)
        frame_3.grid(row=4, column=0, sticky="nsew")
   
        
        self.label = tk.Label(frame_3, text="ここに画像(jpg, jpeg, png, bmp)をドロップ", relief="ridge")
        self.label.drop_target_register(DND_FILES)
        self.label.dnd_bind("<<Drop>>", self.on_drop)
        self.label.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=100, pady=0)
        self.entry = tk.Entry(frame_3)
        self.entry.grid(row=1, column=0, sticky="e", padx=0, pady=15)
        self.button = tk.Button(frame_3, text="JANコードから探す", command=self.search_jan)
        self.button.grid(row=1, column=1, sticky="w", padx=0, pady=15)

        
    def on_drop(self, image):
        extension = ('.jpg', '.jpeg', '.png', '.bmp')
        image_path = image.data
        
        if '} {' in image.data:
            messagebox.showwarning(title='error', message='画像は一件ずつドロップしてください')
            return
            
        if image_path[0]=='{' and image_path[-1]=='}':
            image_path = image_path[1:-1]

        if not image_path.lower().endswith(extension):
            messagebox.showwarning(title='error', message='有効な画像ファイルをドロップしてください')
            return
                
        jan = self.scan_barcode(image_path)

        if jan is None:
            messagebox.showwarning(title='error', message='画像からバーコードが読み取れませんでした')

        else:
            product_info = self.get_prod(jan)
        
            if product_info is None:
                messagebox.showwarning(title='error', message='商品が見つかりませんでした')
                return

            self.update_display(product_info, jan)


    def scan_barcode(self, image_path):
        img = Image.open(image_path)
        decode_result = decode(img)

        if not decode_result:
            return None

        barcode = decode_result[0]
        
        if barcode.type not in ("EAN13", "EAN8"):
            return None

        jan = barcode.data.decode('utf-8')
        return jan

    
    def get_prod(self, jan):
        url = f"https://www.tajimaya-cc.net/?s={jan}&search-type=products"
        response = requests.get(url)
        html = response.text
        
        soup = BeautifulSoup(html, "html.parser")
        li = soup.select_one("ul.prod_list li")
        
        if not li:
            return None
        else:
            name = li.find("p", class_="tit_product").get_text(strip=True)
            price = li.find("span", class_="price").get_text(strip=True)
            image_url = li.find("img")["src"]

            return{
                "prod_name":name,
                "prod_price":price,
                "prod_image":image_url
            }


    def search_jan(self):
        jan = self.entry.get()

        if not jan:
            messagebox.showwarning("error", "JANコードを入力してください")
            return

        product_info = self.get_prod(jan)
        
        if product_info is None:
            messagebox.showwarning(title='error', message='商品が見つかりませんでした')
            return

        self.update_display(product_info, jan)

    
    def update_display(self, product_info, jan):
        
        self.update_image(product_info["prod_image"])

        winsound.Beep(2000, 100)
        
        self.name.config(text="商品名：" + product_info["prod_name"])
        self.price.config(text="価格：" + product_info["prod_price"])
        self.JAN.config(text="JAN：" + jan)
        self.listbox.insert(tk.END, product_info["prod_name"])


    def update_image(self, image_url):
        response_image = requests.get(image_url)
        
        img_data = Image.open(io.BytesIO(response_image.content))
        img_data.thumbnail((250, 250), Image.LANCZOS) 
        prod_image = ImageTk.PhotoImage(img_data)
        
        self.image.config(text="", image=prod_image)
        self.tk_image = prod_image



Application().mainloop()