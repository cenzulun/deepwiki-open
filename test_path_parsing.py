#!/usr/bin/env python3
"""
测试路径解析功能（不依赖外部API）
"""

import os
import sys
import pathlib

def test_path_parsing():
    """测试路径解析逻辑"""
    print("=" * 50)
    print("测试路径解析功能")
    print("=" * 50)
    print()

    # 模拟前端的路径解析逻辑
    def parse_repository_input(input_str):
        """模拟前端parseRepositoryInput函数的逻辑"""
        input_str = input_str.strip()

        # 处理 Windows 绝对路径
        windows_path_regex = r'^[a-zA-Z]:\\(?:[^\\/:*?"<>|\r\n]+\\)*[^\\/:*?"<>|\r\n]*$'
        # 处理 Unix/Linux 绝对路径
        unix_path_regex = r'^\/(?:[^\/\0]+\/)*[^\/\0]*$'
        # 简单的 owner/repo 格式
        owner_repo_regex = r'^([\w\-\.]+)\/([\w\-\.]+)$'
        # 支持您的 GitHub 仓库格式
        your_github_regex = r'^mac\/github-local\/([^\/]+)$'

        import re

        # 测试不同路径格式
        if re.match(windows_path_regex, input_str):
            return {"type": "local", "status": "Windows路径", "path": input_str}
        elif re.match(unix_path_regex, input_str):
            return {"type": "local", "status": "Unix/Linux路径", "path": input_str}
        elif re.match(your_github_regex, input_str):
            match = re.match(your_github_regex, input_str)
            return {"type": "github", "status": "您的GitHub仓库", "owner": "mac", "repo": match.group(1)}
        elif re.match(owner_repo_regex, input_str):
            match = re.match(owner_repo_regex, input_str)
            return {"type": "github", "status": "标准owner/repo格式", "owner": match.group(1), "repo": match.group(2)}
        else:
            return {"type": "unknown", "status": "未知格式", "path": input_str}

    # 测试用例
    test_cases = [
        # 本地路径
        ("/Users/mac/github-local/deepwiki-open-main", "项目根目录绝对路径"),
        ("/tmp", "系统临时目录"),
        ("./api", "相对路径 - api目录"),
        ("./src", "相对路径 - src目录"),
        ("../test", "相对路径 - 上级test目录"),
        (".", "当前目录"),

        # 您的GitHub仓库格式
        ("mac/github-local/deepwiki-open-main", "您的GitHub仓库格式"),
        ("mac/github-local/my-project", "您的GitHub仓库格式 - 项目"),

        # 标准owner/repo格式
        ("facebook/react", "标准GitHub格式"),
        ("microsoft/vscode", "标准GitHub格式"),
        ("openai/gym", "标准GitHub格式"),

        # URL格式
        ("https://github.com/mac/github-local/deepwiki-open-main", "完整GitHub URL"),
        ("https://gitlab.com/gitlab-org/gitlab", "GitLab URL"),

        # Windows路径（如果在Windows系统）
        # ("C:\\Users\\username\\project", "Windows路径"),

        # 无效格式
        ("invalid://path", "无效URL"),
        ("", "空字符串"),
    ]

    # 运行测试
    for i, (test_input, description) in enumerate(test_cases, 1):
        result = parse_repository_input(test_input)

        print(f"测试 {i:2d}: {description}")
        print(f"      输入: '{test_input}'")
        print(f"      结果: {result['status']} ({result['type']})")

        # 验证路径是否实际存在（对于本地路径）
        if result['type'] == 'local' and 'path' in result:
            try:
                path_obj = pathlib.Path(result['path']).expanduser().resolve()
                exists = path_obj.exists()
                is_dir = path_obj.is_dir() if exists else False
                status_icon = "✅" if exists and is_dir else "❌"
                print(f"      验证: {status_icon} {'存在且是目录' if exists and is_dir else '不存在或不是目录'}")
            except Exception as e:
                print(f"      验证: ⚠️  路径检查错误: {e}")

        print()

def test_api_backend_logic():
    """测试后端API处理逻辑"""
    print("=" * 50)
    print("测试后端API路径处理逻辑")
    print("=" * 50)
    print()

    # 模拟后端API的路径处理
    def simulate_local_repo_processing(path):
        """模拟后端API的本地仓库处理逻辑"""
        try:
            # 模拟pathlib路径处理
            input_path = pathlib.Path(path).expanduser().resolve()

            print(f"输入路径: {path}")
            print(f"解析后路径: {input_path}")

            # 检查路径是否存在
            if not input_path.exists():
                return {"success": False, "error": f"目录不存在: {path}"}

            # 确保是目录
            if not input_path.is_dir():
                return {"success": False, "error": f"路径不是目录: {path}"}

            # 模拟文件扫描
            file_count = 0
            readme_found = False
            sample_files = []

            for root, dirs, files in os.walk(input_path):
                # 排除隐藏目录和虚拟环境目录
                dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__'
                          and d != 'node_modules' and d != '.venv' and d != 'venv']

                for file in files:
                    if file.startswith('.') or file in ['__init__.py', '.DS_Store']:
                        continue

                    if any(file.endswith(ext) for ext in ['.pyc', '.pyo', '.class']):
                        continue

                    file_count += 1
                    if len(sample_files) < 5:  # 只收集前5个文件作为示例
                        rel_dir = os.path.relpath(root, input_path)
                        rel_file = os.path.join(rel_dir, file) if rel_dir != '.' else file
                        sample_files.append(rel_file)

                    # 查找README文件
                    if file.lower().startswith('readme') and not readme_found:
                        readme_found = True

            return {
                "success": True,
                "file_count": file_count,
                "readme_found": readme_found,
                "sample_files": sample_files
            }

        except PermissionError:
            return {"success": False, "error": f"权限不足，无法访问路径: {path}"}
        except Exception as e:
            return {"success": False, "error": f"处理路径时发生错误: {str(e)}"}

    # 测试几个本地路径
    test_paths = [
        ".",
        "./api",
        "./src",
        "/tmp",
        "/nonexistent/path"  # 应该失败
    ]

    for i, path in enumerate(test_paths, 1):
        print(f"后端测试 {i}: {path}")
        result = simulate_local_repo_processing(path)

        if result["success"]:
            print(f"          ✅ 处理成功")
            print(f"          📁 文件数量: {result['file_count']}")
            print(f"          📄 README: {'找到' if result['readme_found'] else '未找到'}")
            if result['sample_files']:
                print(f"          📋 示例文件: {', '.join(result['sample_files'])}")
        else:
            print(f"          ❌ 处理失败: {result['error']}")
        print()

def main():
    """主测试函数"""
    print("DeepWiki-Open 路径解析功能测试")
    print("此测试不需要API服务器运行")
    print()

    # 测试路径解析逻辑
    test_path_parsing()

    # 测试后端API逻辑
    test_api_backend_logic()

    print("=" * 50)
    print("测试完成")
    print("=" * 50)
    print()
    print("如果测试通过，说明路径解析功能正常。")
    print("要测试完整的API功能，请启动后端服务：")
    print("  python -m api.main")
    print("然后运行:")
    print("  python3 test_local_path.py")

if __name__ == "__main__":
    main()