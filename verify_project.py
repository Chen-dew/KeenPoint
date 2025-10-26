"""
项目结构验证脚本
检查所有必要的文件和目录是否存在
"""

import os
import sys

def check_structure():
    """检查项目结构"""
    print("🔍 检查项目结构...\n")
    
    required_files = [
        "app/__init__.py",
        "app/main.py",
        "app/api/__init__.py",
        "app/api/routes.py",
        "app/api/upload.py",
        "app/api/analysis.py",
        "app/api/image_manager.py",
        "app/api/ppt_generator.py",
        "app/core/__init__.py",
        "app/core/config.py",
        "app/core/logger.py",
        "app/core/utils.py",
        "app/services/__init__.py",
        "app/services/parser_service.py",
        "app/services/nlp_service.py",
        "app/services/image_service.py",
        "app/services/ppt_service.py",
        "app/models/__init__.py",
        "app/models/schema.py",
        "app/models/db.py",
        "tests/__init__.py",
        "tests/conftest.py",
        "tests/test_upload.py",
        "tests/test_analysis.py",
        "tests/test_ppt.py",
        "requirements.txt",
        "README.md",
        ".gitignore",
    ]
    
    missing_files = []
    existing_files = []
    
    for file in required_files:
        if os.path.exists(file):
            existing_files.append(file)
            print(f"✅ {file}")
        else:
            missing_files.append(file)
            print(f"❌ {file}")
    
    print(f"\n{'='*60}")
    print(f"📊 统计结果:")
    print(f"  ✅ 已存在: {len(existing_files)}/{len(required_files)}")
    print(f"  ❌ 缺失: {len(missing_files)}/{len(required_files)}")
    print(f"{'='*60}\n")
    
    if missing_files:
        print("⚠️ 以下文件缺失:")
        for file in missing_files:
            print(f"  - {file}")
        return False
    else:
        print("🎉 项目结构完整！")
        return True

def check_imports():
    """检查关键导入是否正常"""
    print("\n🔍 检查模块导入...\n")
    
    try:
        # 检查核心模块
        from app.core import config, logger, utils
        print("✅ app.core 模块导入成功")
        
        # 检查服务模块
        from app.services import parser_service, nlp_service, image_service, ppt_service
        print("✅ app.services 模块导入成功")
        
        # 检查模型模块
        from app.models import schema, db
        print("✅ app.models 模块导入成功")
        
        # 检查 API 模块
        from app.api import routes, upload, analysis, image_manager, ppt_generator
        print("✅ app.api 模块导入成功")
        
        # 检查主应用
        from app.main import app
        print("✅ app.main 模块导入成功")
        
        print("\n🎉 所有模块导入成功！")
        return True
    
    except ImportError as e:
        print(f"\n❌ 导入失败: {e}")
        print("\n💡 提示: 请先安装依赖: pip install -r requirements.txt")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("  Academic Paper Assistant - 项目验证")
    print("=" * 60)
    print()
    
    # 检查结构
    structure_ok = check_structure()
    
    # 检查导入
    if structure_ok:
        imports_ok = check_imports()
        
        if imports_ok:
            print("\n" + "=" * 60)
            print("✅ 项目验证通过！可以启动服务了。")
            print("=" * 60)
            print("\n📝 下一步:")
            print("  1. 运行 'uvicorn app.main:app --reload' 启动服务")
            print("  2. 访问 http://127.0.0.1:8000/docs 查看 API 文档")
            print()
            return 0
        else:
            print("\n⚠️ 部分模块导入失败，请检查依赖安装。")
            return 1
    else:
        print("\n❌ 项目结构不完整，请检查文件。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
