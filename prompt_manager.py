import tkinter as tk
from tkinter import ttk, messagebox
from ttkbootstrap import Style
from ttkbootstrap.scrolled import ScrolledText # 带滚轮的文本框
import json
import os

JSON_FILE = 'prompts.json'

class PromptManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("提示词管理器 v1.0")
        self.root.geometry("800x550")

        self.data = self.load_data()

        # ---------- 界面布局 ----------
        
        # 主框架，分为左右两栏
        self.main_paned_window = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        self.main_paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- 左侧栏：类别、搜索、列表 ---
        self.left_frame = ttk.Frame(self.main_paned_window, padding=10)
        self.main_paned_window.add(self.left_frame, weight=1)

        # 类别选择
        ttk.Label(self.left_frame, text="选择类别:", font=("-size", 10)).pack(anchor=tk.W)
        self.category_combo = ttk.Combobox(self.left_frame, state="readonly", font=("-size", 10))
        self.category_combo.pack(fill=tk.X, pady=(5, 10))
        self.category_combo.bind("<<ComboboxSelected>>", self.on_category_select)

        # 搜索Key
        ttk.Label(self.left_frame, text="搜索Key:", font=("-size", 10)).pack(anchor=tk.W)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self.left_frame, textvariable=self.search_var, font=("-size", 10))
        self.search_entry.pack(fill=tk.X, pady=(5, 5))
        self.search_button = ttk.Button(self.left_frame, text="搜索", command=self.search_key, style="outline")
        self.search_button.pack(fill=tk.X, pady=(0, 10))
        # 绑定回车键搜索
        self.search_entry.bind("<Return>", lambda e: self.search_key())


        # 提示词Key列表
        self.listbox_frame = ttk.Frame(self.left_frame) # 用于容纳列表和滚动条
        self.listbox_frame.pack(fill=tk.BOTH, expand=True)
        
        self.list_scrollbar = ttk.Scrollbar(self.listbox_frame, orient=tk.VERTICAL)
        self.prompt_listbox = tk.Listbox(self.listbox_frame, yscrollcommand=self.list_scrollbar.set, font=("-size", 11), selectbackground="#0078d4")
        self.list_scrollbar.config(command=self.prompt_listbox.yview)
        
        self.list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.prompt_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.prompt_listbox.bind("<<ListboxSelect>>", self.on_listbox_select)


        # --- 右侧栏：编辑区和按钮 ---
        self.right_frame = ttk.Frame(self.main_paned_window, padding=10)
        self.main_paned_window.add(self.right_frame, weight=2)

        # Key (键)
        ttk.Label(self.right_frame, text="Key (键):", font=("-size", 10)).pack(anchor=tk.W)
        self.key_var = tk.StringVar()
        self.key_entry = ttk.Entry(self.right_frame, textvariable=self.key_var, font=("-size", 10))
        self.key_entry.pack(fill=tk.X, pady=(5, 10))

        # Value (值 - 提示词)
        ttk.Label(self.right_frame, text="Value (提示词):", font=("-size", 10)).pack(anchor=tk.W)
        # 使用 ScrolledText 自动添加滚动条
        self.value_text = ScrolledText(self.right_frame, height=10, font=("-size", 10), wrap=tk.WORD, autohide=True)
        self.value_text.pack(fill=tk.BOTH, expand=True, pady=(5, 15))

        # 按钮区
        self.button_frame = ttk.Frame(self.right_frame)
        self.button_frame.pack(fill=tk.X)

        self.add_button = ttk.Button(self.button_frame, text="新增", command=self.add_prompt, style="success")
        self.add_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        self.update_button = ttk.Button(self.button_frame, text="更新", command=self.update_prompt, style="info")
        self.update_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        self.delete_button = ttk.Button(self.button_frame, text="删除", command=self.delete_prompt, style="danger")
        self.delete_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        self.clear_button = ttk.Button(self.button_frame, text="清空", command=self.clear_fields, style="secondary.Outline")
        self.clear_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        # ---------- 初始加载 ----------
        self.populate_categories()
        # 默认选中第一个类别
        if self.category_combo['values']:
            self.category_combo.current(0)
            self.on_category_select()

    # ---------- 核心功能函数 ----------

    def load_data(self):
        """加载JSON数据"""
        if not os.path.exists(JSON_FILE):
            messagebox.showerror("错误", f"{JSON_FILE} 未找到！")
            return {}
        try:
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            messagebox.showerror("错误", f"{JSON_FILE} 数据格式损坏！")
            return {}
        except Exception as e:
            messagebox.showerror("错误", f"加载数据失败: {e}")
            return {}

    def save_data(self):
        """保存JSON数据"""
        try:
            with open(JSON_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("错误", f"保存数据失败: {e}")

    def populate_categories(self):
        """填充类别下拉框"""
        categories = list(self.data.keys())
        self.category_combo['values'] = categories

    def populate_listbox(self, filter_key=None):
        """根据类别和搜索词填充列表"""
        self.prompt_listbox.delete(0, tk.END)
        category = self.category_combo.get()
        if not category:
            return
        
        keys = self.data.get(category, {}).keys()
        
        # 过滤
        if filter_key:
            filtered_keys = [k for k in keys if filter_key.lower() in k.lower()]
        else:
            filtered_keys = list(keys)
            
        # 填充
        for key in sorted(filtered_keys):
            self.prompt_listbox.insert(tk.END, key)

    def on_category_select(self, event=None):
        """切换类别时触发"""
        self.search_var.set("") # 清空搜索框
        self.populate_listbox()
        self.clear_fields()

    def on_listbox_select(self, event=None):
        """选中列表项时触发"""
        try:
            selected_indices = self.prompt_listbox.curselection()
            if not selected_indices:
                return
            
            selected_key = self.prompt_listbox.get(selected_indices[0])
            category = self.category_combo.get()
            value = self.data[category][selected_key]
            
            self.key_var.set(selected_key)
            self.value_text.delete('1.0', tk.END)
            self.value_text.insert('1.0', value)
        except Exception as e:
            # 切换类别或搜索时，此事件可能在列表清空时触发，忽略错误
            pass

    def search_key(self):
        """执行搜索"""
        filter_term = self.search_var.get()
        self.populate_listbox(filter_key=filter_term)
        self.clear_fields()

    def clear_fields(self):
        """清空右侧编辑区"""
        self.key_var.set("")
        self.value_text.delete('1.0', tk.END)
        # 取消列表框的选中状态
        self.prompt_listbox.selection_clear(0, tk.END)

    def add_prompt(self):
        """新增提示词"""
        category = self.category_combo.get()
        key = self.key_var.get().strip()
        value = self.value_text.get('1.0', tk.END).strip()

        if not category or not key or not value:
            messagebox.showwarning("警告", "类别、Key和Value均不能为空！")
            return
            
        if category not in self.data:
            self.data[category] = {}

        if key in self.data[category]:
            messagebox.showwarning("警告", f"Key '{key}' 在 '{category}' 类别中已存在！")
            return
            
        self.data[category][key] = value
        self.save_data()
        self.populate_listbox()
        
        # 自动选中新增的项
        for i, item in enumerate(self.prompt_listbox.get(0, tk.END)):
            if item == key:
                self.prompt_listbox.select_set(i)
                self.prompt_listbox.see(i)
                break
                
        messagebox.showinfo("成功", "新增成功！")

    def update_prompt(self):
        """更新提示词"""
        category = self.category_combo.get()
        new_key = self.key_var.get().strip()
        new_value = self.value_text.get('1.0', tk.END).strip()

        selected_indices = self.prompt_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("警告", "请先在左侧列表中选择要更新的项！")
            return
            
        original_key = self.prompt_listbox.get(selected_indices[0])

        if not category or not new_key or not new_value:
            messagebox.showwarning("警告", "类别、Key和Value均不能为空！")
            return

        # 如果Key被修改了
        if original_key != new_key:
            # 检查新Key是否已存在
            if new_key in self.data[category]:
                messagebox.showwarning("警告", f"Key '{new_key}' 已存在！")
                return
            # 删除旧Key
            del self.data[category][original_key]
        
        # 更新/添加新Key
        self.data[category][new_key] = new_value
        self.save_data()
        
        # 刷新列表并重新选中
        self.populate_listbox()
        for i, item in enumerate(self.prompt_listbox.get(0, tk.END)):
            if item == new_key:
                self.prompt_listbox.select_set(i)
                self.prompt_listbox.see(i)
                break
                
        messagebox.showinfo("成功", "更新成功！")

    def delete_prompt(self):
        """删除提示词"""
        selected_indices = self.prompt_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("警告", "请先在左侧列表中选择要删除的项！")
            return
            
        key_to_delete = self.prompt_listbox.get(selected_indices[0])
        category = self.category_combo.get()
        
        if not messagebox.askyesno("确认删除", f"确定要删除 '{category}' -> '{key_to_delete}' 吗？"):
            return
            
        if key_to_delete in self.data[category]:
            del self.data[category][key_to_delete]
            self.save_data()
            self.populate_listbox()
            self.clear_fields()
            messagebox.showinfo("成功", "删除成功！")
        else:
            messagebox.showerror("错误", "未找到要删除的项，数据可能已不同步。")


if __name__ == "__main__":
    # 使用 'litera' 主题，感觉比较清爽
    # 其他可选主题: 'cosmo', 'flatly', 'journal', 'darkly', 'superhero', 'cyborg' 等
    root = Style(theme="litera").master 
    app = PromptManagerApp(root)
    root.mainloop()