#!/usr/bin/env python3
"""
测试本地路径解析功能
"""

import sys
import os
import asyncio
import httpx
import json

# 添加api目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_local_path_api(path):
    """测试本地路径API"""
    print(f"测试本地路径: {path}")

    try:
        async with httpx.AsyncClient() as client:
            # 测试API端点
            response = await client.get(
                f"http://localhost:8001/local_repo/structure",
                params={"path": path},
                timeout=30.0
            )

            if response.status_code == 200:
                data = response.json()
                print(f"✅ 成功处理路径: {path}")
                print(f"   - 解析后的路径: {data.get('resolved_path', 'N/A')}")
                print(f"   - 文件数量: {data.get('file_count', 0)}")
                print(f"   - README文件: {'有' if data.get('readme') else '无'}")
                print(f"   - 文件树预览: {data.get('file_tree', '')[:200]}...")
                print()
                return True
            else:
                print(f"❌ API请求失败: {response.status_code}")
                print(f"   错误信息: {response.text}")
                print()
                return False

    except httpx.ConnectError:
        print("❌ 无法连接到API服务器，请确保后端服务正在运行 (python -m api.main)")
        print()
        return False
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        print()
        return False

def test_path_parsing():
    """测试路径解析逻辑"""
    print("=" * 50)
    print("测试路径解析逻辑")
    print("=" * 50)

    # 测试各种路径格式
    test_paths = [
        # 当前项目路径
        ".",
        "./api",
        "./src",

        # 绝对路径（如果存在）
        "/Users/mac/github-local/deepwiki-open-main",
        "/tmp",

        # 相对路径
        "..",
        "../test",

        # 您的GitHub仓库格式
        "mac/github-local/deepwiki-open-main",

        # 不存在的路径（应该失败）
        "/nonexistent/path",
        "invalid://path",
    ]

    results = []
    for path in test_paths:
        try:
            import pathlib
            # 模拟路径解析逻辑
            input_path = pathlib.Path(path).expanduser().resolve()
            exists = input_path.exists()
            is_dir = input_path.is_dir()

            status = "✅" if exists and is_dir else "❌"
            print(f"{status} {path} -> {input_path} ({'存在' if exists else '不存在'}, {'目录' if is_dir else '不是目录'})")
            results.append((path, exists and is_dir))

        except Exception as e:
            print(f"❌ {path} -> 错误: {str(e)}")
            results.append((path, False))

    return results

async def main():
    """主测试函数"""
    print("=" * 50)
    print("DeepWiki-Open 本地路径功能测试")
    print("=" * 50)
    print()

    # 首先测试路径解析逻辑
    path_results = test_path_parsing()

    print("\n" + "=" * 50)
    print("测试API端点")
    print("=" * 50)
    print()

    # 选择一些存在的路径进行API测试
    api_test_paths = []
    for path, exists in path_results:
        if exists:
            api_test_paths.append(path)
            if len(api_test_paths) >= 3:  # 最多测试3个路径
                break

    if not api_test_paths:
        print("❌ 没有找到有效的测试路径，请确保您在项目根目录运行此脚本")
        return

    # 测试每个有效路径
    success_count = 0
    for path in api_test_paths:
        if await test_local_path_api(path):
            success_count += 1

    # 总结
    print("=" * 50)
    print("测试总结")
    print("=" * 50)
    print(f"✅ 成功: {success_count}/{len(api_test_paths)} 个路径测试通过")

    if success_count == len(api_test_paths):
        print("🎉 本地路径功能测试全部通过！")
    else:
        print("⚠️  部分测试失败，请检查错误信息")

if __name__ == "__main__":
    # 运行测试
    asyncio.run(main())