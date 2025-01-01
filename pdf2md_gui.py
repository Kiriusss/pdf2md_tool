import tkinter as tk
from tkinter import filedialog, messagebox
import requests
import json
import os

def load_config(config_path="config.json") -> dict:
    """
    从配置文件中加载 app_id 和 secret_code。
    文件格式示例：
    {
      "app_id": "your_app_id",
      "secret_code": "your_secret_code"
    }
    """
    if not os.path.isfile(config_path):
        raise FileNotFoundError(f"配置文件 {config_path} 不存在，请检查路径或创建该文件。")
    
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if not data.get("app_id") or not data.get("secret_code"):
        raise ValueError("配置文件中缺少 app_id 或 secret_code。")
    
    return data

def pdf_to_markdown(
    file_path: str,
    app_id: str,
    secret_code: str,
    pdf_pwd: str = "",
    page_start: int = 1,
    page_count: int = 1000
) -> str:
    """
    将本地 PDF 文件上传至 Textin 接口进行分析，并获取 Markdown 字符串。
    """
    url = "https://api.textin.com/ai/service/v1/pdf_to_markdown"

    headers = {
        "x-ti-app-id": app_id,
        "x-ti-secret-code": secret_code,
        "Content-Type": "application/octet-stream",
    }

    params = {
        "pdf_pwd": pdf_pwd,           # 如果 PDF 加密，可以填写密码
        "page_start": page_start,     # 起始页
        "page_count": page_count,     # 页数（不是“结束页”，而是从page_start起数多少页）
        "apply_document_tree": 1,     
        "markdown_details": 1,        
        "table_flavor": "html",       
        "parse_mode": "scan",         
        "get_image": "none"           
    }

    with open(file_path, "rb") as f:
        file_data = f.read()

    response = requests.post(
        url,
        headers=headers,
        params=params,
        data=file_data
    )

    if response.status_code == 200:
        try:
            res_json = response.json()
            if res_json.get("code") == 200:
                result = res_json.get("result", {})
                return result.get("markdown", "")
            else:
                error_msg = res_json.get("message", "接口返回异常，但 code != 200")
                raise Exception(f"接口调用失败: {error_msg}")
        except json.JSONDecodeError:
            raise Exception(f"返回内容无法解析为 JSON: {response.text}")
    else:
        raise Exception(f"HTTP 状态码非 200，实际为 {response.status_code}, 原因: {response.text}")

def select_pdf_file():
    """让用户选择 PDF 文件。"""
    file_path = filedialog.askopenfilename(
        title="选择 PDF 文件",
        filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")]
    )
    if file_path:
        entry_pdf_path.delete(0, tk.END)
        entry_pdf_path.insert(0, file_path)

def select_output_directory():
    """让用户选择输出 Markdown 文件的目录。"""
    directory = filedialog.askdirectory(title="选择输出目录")
    if directory:
        entry_output_dir.delete(0, tk.END)
        entry_output_dir.insert(0, directory)

def start_conversion():
    """执行 PDF -> Markdown 转换，并保存文件。"""
    pdf_path = entry_pdf_path.get().strip()
    pdf_pwd = entry_pdf_pwd.get().strip()
    page_start_str = entry_page_start.get().strip()
    page_end_str = entry_page_end.get().strip()
    output_dir = entry_output_dir.get().strip()

    # 基础校验
    if not pdf_path or not os.path.isfile(pdf_path):
        messagebox.showwarning("警告", "请选择正确的 PDF 文件路径")
        return
    if not output_dir or not os.path.isdir(output_dir):
        messagebox.showwarning("警告", "请选择正确的输出目录")
        return

    # 默认识别整个文档
    page_start = 1
    page_count = 1000  # Textin 默认限制一次最多1000页
    # 如果用户填写了起始页和结束页，则只转换对应区间
    if page_start_str and page_end_str:
        try:
            start_num = int(page_start_str)
            end_num = int(page_end_str)
            if start_num < 1 or end_num < start_num:
                raise ValueError("页码不合法")
            page_start = start_num
            page_count = end_num - start_num + 1
        except ValueError:
            messagebox.showwarning("警告", "请在起始页和结束页中输入正确的数字范围")
            return

    # 加载配置文件中的 app_id 和 secret_code
    try:
        config = load_config()
        app_id = config["app_id"]
        secret_code = config["secret_code"]
    except Exception as e:
        messagebox.showerror("错误", f"加载配置文件失败：\n{str(e)}")
        return

    try:
        md_text = pdf_to_markdown(
            file_path=pdf_path,
            app_id=app_id,
            secret_code=secret_code,
            pdf_pwd=pdf_pwd,
            page_start=page_start,
            page_count=page_count
        )
        # 在输出目录下生成与 PDF 同名的 .md 文件
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_file = os.path.join(output_dir, pdf_name + ".md")

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(md_text)

        messagebox.showinfo("完成", f"转换成功！Markdown 文件已保存到:\n{output_file}")
    except Exception as e:
        messagebox.showerror("错误", f"转换失败，原因：\n{str(e)}")

# -----------------------------
# 下面是 GUI 布局部分
# -----------------------------
root = tk.Tk()
root.title("PDF 转 Markdown")

# 创建控件
label_pdf_path = tk.Label(root, text="PDF 文件路径:")
entry_pdf_path = tk.Entry(root, width=40)
btn_select_pdf = tk.Button(root, text="浏览...", command=select_pdf_file)

label_pdf_pwd = tk.Label(root, text="PDF 密码(可选):")
entry_pdf_pwd = tk.Entry(root, width=20)

label_page_start = tk.Label(root, text="起始页(可选):")
entry_page_start = tk.Entry(root, width=10)

label_page_end = tk.Label(root, text="结束页(可选):")
entry_page_end = tk.Entry(root, width=10)

label_output_dir = tk.Label(root, text="输出目录:")
entry_output_dir = tk.Entry(root, width=40)
btn_select_dir = tk.Button(root, text="浏览...", command=select_output_directory)

btn_start = tk.Button(root, text="开始转换", width=15, command=start_conversion)

# 布局
padx = 5
pady = 3

label_pdf_path.grid(row=0, column=0, sticky="e", padx=padx, pady=pady)
entry_pdf_path.grid(row=0, column=1, padx=padx, pady=pady)
btn_select_pdf.grid(row=0, column=2, padx=padx, pady=pady)

label_pdf_pwd.grid(row=1, column=0, sticky="e", padx=padx, pady=pady)
entry_pdf_pwd.grid(row=1, column=1, padx=padx, pady=pady)

label_page_start.grid(row=2, column=0, sticky="e", padx=padx, pady=pady)
entry_page_start.grid(row=2, column=1, sticky="w", padx=padx, pady=pady)

label_page_end.grid(row=3, column=0, sticky="e", padx=padx, pady=pady)
entry_page_end.grid(row=3, column=1, sticky="w", padx=padx, pady=pady)

label_output_dir.grid(row=4, column=0, sticky="e", padx=padx, pady=pady)
entry_output_dir.grid(row=4, column=1, padx=padx, pady=pady)
btn_select_dir.grid(row=4, column=2, padx=padx, pady=pady)

btn_start.grid(row=5, column=0, columnspan=3, pady=10)

root.mainloop()
