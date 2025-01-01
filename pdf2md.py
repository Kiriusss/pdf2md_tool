import requests
import json

def pdf_to_markdown(
    file_path: str,
    app_id: str,
    secret_code: str,
    pdf_pwd: str = "",
    page_start: int = 1,
    page_count: int = 5
):
    """
    将本地 PDF 文件上传至 Textin 接口进行分析，并获取 Markdown 字符串。
    你可以根据业务需要，调整或增加更多可选参数。
    """
    # 1. 设置请求地址
    url = "https://api.textin.com/ai/service/v1/pdf_to_markdown"

    # 2. 设置请求头（必须包含 x-ti-app-id, x-ti-secret-code）
    headers = {
        "x-ti-app-id": app_id,
        "x-ti-secret-code": secret_code,
        # 当上传二进制文件时，需要指定 content-type
        "Content-Type": "application/octet-stream",
    }

    # 3. 可选：将需要的参数放入 URL 查询参数中
    #    若无需传参，可以不添加 params，直接 post
    params = {
        "pdf_pwd": pdf_pwd,            # 若 PDF 需要密码，可在此传入
        "page_start": page_start,      # 从第几页开始识别
        "page_count": page_count,      # 要识别的页数
        # 下面是一些常见可选参数，你可根据需要打开或关闭
        "apply_document_tree": 1,      # 是否生成标题(默认为1)
        "markdown_details": 1,         # 是否生成markdown details(默认为1)
        "table_flavor": "html",        # 表格语法(html 或 md)，默认 html
        "parse_mode": "scan",          # PDF解析模式 (auto 或 scan)，默认 scan
        "get_image": "none",           # 是否返回图片 (none、page、objects、both)，默认 none
        # 如果你需要将图片直接以Base64方式返回，可加:
        # "image_output_type": "base64str",
    }

    # 4. 读取 PDF 文件的二进制内容并发起请求
    with open(file_path, "rb") as f:
        file_data = f.read()

    # 发起 POST 请求
    response = requests.post(
        url,
        headers=headers,
        params=params,
        data=file_data
    )

    # 5. 解析响应结果
    if response.status_code == 200:
        try:
            res_json = response.json()
            # 判断接口返回是否成功（code=200 表示成功）
            if res_json.get("code") == 200:
                # 获取识别结果
                result = res_json.get("result", {})
                markdown_text = result.get("markdown", "")

                # 也可以查看更多字段，比如 total_page_number 等
                total_pages = result.get("total_page_number", 0)
                print(f"PDF共 {total_pages} 页，本次成功识别 Markdown。")

                # 返回 Markdown 内容
                return markdown_text
            else:
                error_msg = res_json.get("message", "接口返回异常，但 code != 200")
                raise Exception(f"接口调用失败: {error_msg}")
        except json.JSONDecodeError:
            raise Exception(f"返回内容无法解析为 JSON: {response.text}")
    else:
        raise Exception(f"HTTP 状态码非 200，实际为 {response.status_code}, 原因: {response.text}")


def main():
    # 从 Textin 获取到的开发者信息（请务必自行替换）
    YOUR_APP_ID = "377af60d5b09e55de0e853bff821e3bb"
    YOUR_SECRET_CODE = "60c11a5197bc3bc13da34294c4832bf7"

    pdf_file_path = "1.pdf"

    # 调用接口
    try:
        md_result = pdf_to_markdown(
            file_path=pdf_file_path,
            app_id=YOUR_APP_ID,
            secret_code=YOUR_SECRET_CODE,
            pdf_pwd="",       # 如果PDF有密码，请填写
            page_start=1,
            page_count=2      # 假设只识别前2页
        )
        # 如果成功，可将 md_result 写入到 .md 文件
        with open("example_result.md", "w", encoding="utf-8") as f:
            f.write(md_result)
        print("成功将 PDF 转为 Markdown，并保存为 example_result.md")

    except Exception as e:
        print(f"识别失败，错误原因: {str(e)}")

if __name__ == "__main__":
    main()
