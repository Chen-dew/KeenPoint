"""
MinerU 集成验证脚本
检查所有配置和依赖是否正确
"""

import sys
import os

def check_config():
    """检查配置"""
    print("🔍 检查配置...")
    
    try:
        from app.core.config import settings
        
        print(f"  ✅ MINERU_API: {settings.MINERU_API}")
        
        if settings.MINERU_TOKEN and len(settings.MINERU_TOKEN) > 20:
            print(f"  ✅ MINERU_TOKEN: {settings.MINERU_TOKEN[:20]}... (已配置)")
        else:
            print(f"  ⚠️ MINERU_TOKEN: 未配置或无效")
            return False
        
        return True
    except Exception as e:
        print(f"  ❌ 配置加载失败: {str(e)}")
        return False

def check_dependencies():
    """检查依赖包"""
    print("\n🔍 检查依赖包...")
    
    required = [
        ('aiohttp', 'aiohttp'),
        ('aiofiles', 'aiofiles'),
        ('fastapi', 'fastapi'),
        ('fitz', 'PyMuPDF'),
    ]
    
    all_ok = True
    for module, package in required:
        try:
            __import__(module)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - 未安装")
            print(f"     安装: pip install {package}")
            all_ok = False
    
    return all_ok

def check_parser_service():
    """检查解析服务"""
    print("\n🔍 检查解析服务...")
    
    try:
        from app.services.parser_service import parse_pdf_with_mineru
        print("  ✅ parse_pdf_with_mineru 函数已导入")
        
        from app.services.parser_service import parse_document
        print("  ✅ parse_document 函数已导入")
        
        return True
    except Exception as e:
        print(f"  ❌ 导入失败: {str(e)}")
        return False

def check_directories():
    """检查目录结构"""
    print("\n🔍 检查目录结构...")
    
    try:
        from app.core.config import settings
        
        dirs = [
            settings.UPLOAD_DIR,
            settings.OUTPUT_DIR,
            settings.TEMP_DIR,
        ]
        
        for dir_path in dirs:
            if os.path.exists(dir_path):
                print(f"  ✅ {dir_path}")
            else:
                print(f"  ⚠️ {dir_path} - 不存在（将自动创建）")
        
        return True
    except Exception as e:
        print(f"  ❌ 检查失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("  MinerU API 集成验证")
    print("=" * 60)
    print()
    
    results = []
    
    # 检查配置
    results.append(("配置", check_config()))
    
    # 检查依赖
    results.append(("依赖包", check_dependencies()))
    
    # 检查解析服务
    results.append(("解析服务", check_parser_service()))
    
    # 检查目录
    results.append(("目录结构", check_directories()))
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 验证结果:")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    print()
    
    if all_passed:
        print("🎉 所有检查通过！")
        print()
        print("📝 下一步:")
        print("  1. 运行 'python test_mineru.py' 测试解析功能")
        print("  2. 或启动服务: uvicorn app.main:app --reload")
        print()
        return 0
    else:
        print("⚠️ 部分检查未通过，请解决上述问题。")
        print()
        print("💡 常见解决方案:")
        print("  - 依赖缺失: pip install -r requirements.txt")
        print("  - Token 未配置: 复制 .env.example 到 .env 并设置 MINERU_TOKEN")
        print()
        return 1

if __name__ == "__main__":
    sys.exit(main())
