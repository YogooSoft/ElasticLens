"""验证版本号配置"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

try:
    from version import VERSION, VERSION_INFO
    print(f"✅ 后端版本号: {VERSION}")
    print(f"✅ 版本信息: {VERSION_INFO}")
except ImportError as e:
    print(f"❌ 无法导入版本模块: {e}")
    sys.exit(1)

print("\n📋 版本号配置验证完成")