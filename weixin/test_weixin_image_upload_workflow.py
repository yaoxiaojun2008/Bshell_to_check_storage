#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用环境配置和图片目录中的图片测试微信素材上传和草稿创建流程
"""

import os
import requests
import json
import dotenv
from pathlib import Path

# Load environment variables from .env file
dotenv.load_dotenv()

# 从环境变量获取配置
WECHAT_APP_ID = os.getenv("WECHAT_APP_ID")
WECHAT_APP_SECRET = os.getenv("WECHAT_APP_SECRET")

if not WECHAT_APP_ID or not WECHAT_APP_SECRET:
    print("❌ 缺少微信配置信息")
    exit(1)

print(f"✅ 使用配置: AppID: {WECHAT_APP_ID}")

# 微信API配置
TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"
UPLOAD_MATERIAL_URL = "https://api.weixin.qq.com/cgi-bin/material/add_material"
UPLOAD_IMG_URL = "https://api.weixin.qq.com/cgi-bin/media/uploadimg"
DRAFT_URL = "https://api.weixin.qq.com/cgi-bin/draft/add"

def get_access_token():
    """获取微信访问令牌"""
    print("🔑 正在获取微信访问令牌...")
    
    params = {
        'grant_type': 'client_credential',
        'appid': WECHAT_APP_ID,
        'secret': WECHAT_APP_SECRET
    }
    
    try:
        response = requests.get(TOKEN_URL, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if 'errcode' in data:
            print(f"❌ 获取令牌失败: {data['errcode']} - {data.get('errmsg', 'Unknown error')}")
            return None
            
        if 'access_token' not in data:
            print(f"❌ 响应中没有access_token")
            return None
            
        access_token = data['access_token']
        print(f"✅ 成功获取访问令牌")
        
        return access_token
        
    except Exception as e:
        print(f"❌ 获取令牌失败: {e}")
        return None

def upload_permanent_image(access_token, image_path):
    """上传永久图片素材，用于封面图"""
    print(f"🖼️ 正在上传永久图片素材: {image_path}")
    
    upload_url = f"{UPLOAD_MATERIAL_URL}?access_token={access_token}&type=image"
    with open(image_path, 'rb') as f:
        files = {'media': f}
        response = requests.post(upload_url, files=files)
        
    result = response.json()
    if 'media_id' in result:
        print(f"✅ 永久图片素材上传成功，ID: {result['media_id']}")
        return result['media_id']
    else:
        print(f"❌ 永久图片素材上传失败: {result}")
        return None

def upload_content_image(access_token, image_path):
    """上传图文消息内的图片，用于content内容"""
    print(f"🖼️ 正在上传图文消息图片: {image_path}")
    
    upload_img_url = f"{UPLOAD_IMG_URL}?access_token={access_token}"
    with open(image_path, 'rb') as f:
        files = {'media': f}
        response = requests.post(upload_img_url, files=files)
        
    result = response.json()
    if 'url' in result:
        print(f"✅ 图文消息图片上传成功，URL: {result['url']}")
        return result['url']
    else:
        print(f"❌ 图文消息图片上传失败: {result}")
        return None

def create_draft_with_image(access_token, thumb_media_id, content_img_url, title, content):
    """使用上传的图片创建草稿"""
    print(f"📝 正在创建草稿: {title}")
    
    draft_data = {
        "articles": [{
            "title": title,
            "author": "测试作者",
            "digest": "这是一段摘要",
            "content": content,
            "content_source_url": "",
            "thumb_media_id": thumb_media_id,
            "show_cover_pic": 1,
            "need_open_comment": 0,
            "only_fans_can_comment": 0
        }]
    }
    
    url = f"{DRAFT_URL}?access_token={access_token}"
    headers = {'Content-Type': 'application/json; charset=utf-8'}
    
    try:
        response = requests.post(
            url,
            data=json.dumps(draft_data, ensure_ascii=False).encode('utf-8'),
            headers=headers,
            timeout=30
        )
        
        data = response.json()
        print(f"📡 微信接口原始响应: {json.dumps(data, indent=2, ensure_ascii=False)}")

        # 1. 逻辑判断：如果返回中包含 media_id，则视为成功（无论是否有 errcode）
        media_id = data.get('media_id')
        
        if media_id:
            print("✅ 草稿创建成功!")
            # 如果有 item 信息，可以记录日志，没有也不影响逻辑
            if 'item' in data:
                print(f"📊 索引详情: {data['item']}")
            print(f"🆔 草稿 Media ID: {media_id}")
            # return media_id
            return True 
    
        # 2. 如果没有 media_id，则检查是否存在 errcode 报错
        else:
            errcode = data.get('errcode')
            errmsg = data.get('errmsg', '未知错误')
            
            # 处理微信特有的逻辑：即使没有 media_id，只要 errcode 显式为 0 也是成功
            # 但在“新建草稿”接口中，通常 media_id 是伴随成功出现的
            if errcode == 0:
                print("✅ 接口调用成功（但未返回 Media ID）")
                return True 
    
            print(f"❌ 草稿创建失败: {errcode} - {errmsg}")
            
            # IT 专家建议：如果是 40001 (Access Token 过期)，这里可以触发 Token 刷新逻辑
            if errcode == 40001:
                print("💡 提示：Access Token 已失效，请检查 Vercel 环境变量或缓存。")
                
            return None
            
    except Exception as e:
        print(f"❌ 草稿创建失败: {e}")
        return None

def main():
    """主函数"""
    print("🚀 开始测试使用环境配置和图片目录的素材上传和草稿创建流程")
    print("=" * 70)
    
    # 获取图片目录中的所有图片
    img_dir = Path("img")
    if not img_dir.exists():
        print(f"❌ 图片目录不存在: {img_dir}")
        return
    
    image_files = [f for f in img_dir.iterdir() 
                   if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']]
    
    if not image_files:
        print("❌ 图片目录中没有找到图片文件")
        return
    
    print(f"📁 找到 {len(image_files)} 个图片文件")
    
    # 步骤1: 获取访问令牌
    access_token = get_access_token()
    if not access_token:
        print("💥 无法获取访问令牌，测试终止")
        return
    
    # 仅测试前3张图片
    for i, img_file in enumerate(image_files[:3]):
        print(f"\n--- 处理第 {i+1} 张图片: {img_file.name} ---")
        
        # 步骤2: 上传封面图片素材
        thumb_media_id = upload_permanent_image(access_token, str(img_file))
        if not thumb_media_id:
            print(f"💥 无法上传封面图片 {img_file.name}，跳过此图片")
            continue
        
        # 步骤3: 上传内容图片
        content_img_url = upload_content_image(access_token, str(img_file))
        if not content_img_url:
            print(f"💥 无法上传内容图片 {img_file.name}，跳过此图片")
            continue
        
        # 步骤4: 使用素材ID创建草稿
        content_with_img = f"<p>这是一篇使用图片 {img_file.name} 创建的测试草稿内容。</p><p>内容中的图片:</p><img src='{content_img_url}' alt='内容图片'><p>这是图片之后的内容。</p>"
        title = f"测试草稿 - {img_file.name}"
        
        result = create_draft_with_image(access_token, thumb_media_id, content_img_url, title, content_with_img)
        
        if result:
            print(f"🎉 草稿创建成功！草稿ID: {result}")
        else:
            print("💥 草稿创建失败")
        
        print(f"--- {img_file.name} 处理完成 ---")
    
    print("\n" + "=" * 70)
    print("📊 素材上传和草稿创建流程测试完成")
    print("=" * 70)

if __name__ == "__main__":
    main()