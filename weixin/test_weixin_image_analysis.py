#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信图片分析和优化测试脚本
分析wx1.jpg并创建符合微信要求的图片进行测试
"""

import requests
import json
import time
import os
import io
from PIL import Image

# 微信API配置
WECHAT_APP_ID = "your IP"
WECHAT_APP_SECRET = "your serect"

# 微信API端点
TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"
TEMP_MEDIA_URL = "https://api.weixin.qq.com/cgi-bin/media/upload"
DRAFT_URL = "https://api.weixin.qq.com/cgi-bin/draft/add"

def analyze_image(image_path):
    """分析图片信息"""
    print(f"🔍 分析图片: {image_path}")
    
    if not os.path.exists(image_path):
        print(f"❌ 图片文件不存在: {image_path}")
        return None
    
    try:
        # 获取文件大小
        file_size = os.path.getsize(image_path)
        print(f"📏 文件大小: {file_size} bytes ({file_size/1024:.1f} KB)")
        
        # 获取图片尺寸
        with Image.open(image_path) as img:
            width, height = img.size
            format_name = img.format
            mode = img.mode
            
            print(f"🖼️ 图片信息:")
            print(f"   - 尺寸: {width} x {height}")
            print(f"   - 格式: {format_name}")
            print(f"   - 模式: {mode}")
            
            # 微信缩略图要求分析
            print(f"\n📋 微信要求分析:")
            print(f"   - 缩略图要求: 128x128 像素")
            print(f"   - 文件大小: < 64KB")
            print(f"   - 格式: JPG")
            
            # 检查是否符合要求
            size_ok = file_size < 64 * 1024
            format_ok = format_name.upper() in ['JPEG', 'JPG']
            
            print(f"\n✅ 符合性检查:")
            print(f"   - 文件大小: {'✅' if size_ok else '❌'} ({file_size/1024:.1f}KB {'< 64KB' if size_ok else '>= 64KB'})")
            print(f"   - 格式: {'✅' if format_ok else '❌'} ({format_name})")
            
            return {
                'width': width,
                'height': height,
                'size': file_size,
                'format': format_name,
                'mode': mode,
                'size_ok': size_ok,
                'format_ok': format_ok
            }
            
    except Exception as e:
        print(f"❌ 分析图片失败: {e}")
        return None

def create_optimized_thumb(source_path, output_path, size=(128, 128)):
    """创建优化的缩略图"""
    print(f"🛠️ 创建优化缩略图: {size[0]}x{size[1]}")
    
    try:
        with Image.open(source_path) as img:
            # 转换为RGB模式（如果需要）
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 创建缩略图（保持比例）
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # 创建新的正方形图片
            thumb = Image.new('RGB', size, (255, 255, 255))  # 白色背景
            
            # 计算居中位置
            x = (size[0] - img.width) // 2
            y = (size[1] - img.height) // 2
            
            # 粘贴图片到中心
            thumb.paste(img, (x, y))
            
            # 保存为JPEG，质量85
            thumb.save(output_path, 'JPEG', quality=85, optimize=True)
            
            # 检查文件大小
            new_size = os.path.getsize(output_path)
            print(f"✅ 缩略图创建成功:")
            print(f"   - 文件: {output_path}")
            print(f"   - 尺寸: {size[0]}x{size[1]}")
            print(f"   - 大小: {new_size} bytes ({new_size/1024:.1f} KB)")
            
            return output_path
            
    except Exception as e:
        print(f"❌ 创建缩略图失败: {e}")
        return None

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

def upload_optimized_thumb(access_token, image_path):
    """上传优化后的缩略图"""
    print(f"📤 上传优化缩略图: {image_path}")
    
    url = f"{TEMP_MEDIA_URL}?access_token={access_token}&type=thumb"
    
    try:
        with open(image_path, 'rb') as f:
            files = {'media': (os.path.basename(image_path), f, 'image/jpeg')}
            
            response = requests.post(url, files=files, timeout=30)
            data = response.json()
            
            print(f"📡 缩略图上传响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            if 'errcode' in data and data['errcode'] != 0:
                print(f"❌ 缩略图上传失败: {data['errcode']} - {data.get('errmsg', 'Unknown error')}")
                return None
                
            if 'thumb_media_id' in data:
                print(f"✅ 缩略图上传成功: {data['thumb_media_id']}")
                return data['thumb_media_id']
            elif 'media_id' in data:
                print(f"✅ 图片上传成功: {data['media_id']}")
                return data['media_id']
            else:
                print("❌ 响应中没有media_id")
                return None
                
    except Exception as e:
        print(f"❌ 缩略图上传失败: {e}")
        return None

def test_draft_with_optimized_thumb(access_token, thumb_media_id):
    """使用优化缩略图测试草稿"""
    print(f"\n📝 使用优化缩略图测试草稿")
    
    draft_data = {
        "articles": [{
            "title": "优化图片测试草稿",
            "author": "测试作者",
            "digest": "使用优化后的缩略图测试草稿创建",
            "content": "<p>这是使用优化缩略图的测试草稿。</p><p>图片已按微信要求优化为128x128像素。</p>",
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
        print(f"📡 草稿API响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        if data.get('errcode', 0) == 0:
            print(f"✅ 优化图片草稿创建成功!")
            print(f"🆔 Draft Media ID: {data.get('media_id')}")
            return True
        else:
            errcode = data.get('errcode')
            errmsg = data.get('errmsg', '')
            print(f"❌ 优化图片草稿创建失败: {errcode} - {errmsg}")
            return False
            
    except Exception as e:
        print(f"❌ 草稿请求失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 开始微信图片分析和优化测试")
    print("=" * 60)
    
    source_image = "wx1.jpg"
    optimized_thumb = "wx1_thumb_128x128.jpg"
    
    # 步骤1: 分析原始图片
    print("📋 步骤1: 分析原始图片")
    print("=" * 60)
    
    image_info = analyze_image(source_image)
    if not image_info:
        print("💥 无法分析图片，测试终止")
        return
    
    # 步骤2: 创建优化缩略图
    print(f"\n{'=' * 60}")
    print("🛠️ 步骤2: 创建优化缩略图")
    print("=" * 60)
    
    thumb_path = create_optimized_thumb(source_image, optimized_thumb)
    if not thumb_path:
        print("💥 无法创建优化缩略图，测试终止")
        return
    
    # 步骤3: 获取访问令牌
    print(f"\n{'=' * 60}")
    print("🔑 步骤3: 获取访问令牌")
    print("=" * 60)
    
    access_token = get_access_token()
    if not access_token:
        print("💥 无法获取访问令牌，测试终止")
        return
    
    # 步骤4: 上传优化缩略图
    print(f"\n{'=' * 60}")
    print("📤 步骤4: 上传优化缩略图")
    print("=" * 60)
    
    thumb_media_id = upload_optimized_thumb(access_token, thumb_path)
    
    # 步骤5: 测试草稿创建
    if thumb_media_id:
        print(f"\n{'=' * 60}")
        print("📝 步骤5: 测试草稿创建")
        print("=" * 60)
        
        draft_success = test_draft_with_optimized_thumb(access_token, thumb_media_id)
    else:
        draft_success = False
    
    # 总结
    print(f"\n{'=' * 60}")
    print("📊 测试总结")
    print("=" * 60)
    
    print(f"\n📋 测试结果:")
    print(f"   - 原始图片分析: ✅ 成功")
    if image_info:
        print(f"     尺寸: {image_info['width']}x{image_info['height']}")
        print(f"     大小: {image_info['size']/1024:.1f}KB")
        print(f"     格式: {image_info['format']}")
    
    print(f"   - 优化缩略图创建: {'✅ 成功' if thumb_path else '❌ 失败'}")
    print(f"   - 缩略图上传: {'✅ 成功' if thumb_media_id else '❌ 失败'}")
    if thumb_media_id:
        print(f"     Media ID: {thumb_media_id}")
    
    print(f"   - 草稿创建: {'✅ 成功' if draft_success else '❌ 失败'}")
    
    print(f"\n💡 结论:")
    if draft_success:
        print("   🎉 完全成功！优化后的图片可以用于草稿创建")
        print("   - 建议在应用中使用图片优化功能")
        print("   - 缩略图尺寸: 128x128像素")
        print("   - 文件大小: < 64KB")
    elif thumb_media_id:
        print("   ⚠️ 部分成功：图片上传成功但草稿创建失败")
        print("   - 可能是账号权限问题，不是图片问题")
        print("   - 建议继续使用Mock模式")
    else:
        print("   ❌ 图片上传失败，可能是API限制")
        print("   - 建议使用Mock模式进行开发")
    
    # 清理临时文件
    if os.path.exists(optimized_thumb):
        os.remove(optimized_thumb)
        print(f"\n🧹 已清理临时文件: {optimized_thumb}")
    
    print("=" * 60)

if __name__ == "__main__":

    main()
