#!/usr/bin/env python3
"""
测试国产模型配置和集成
"""

import sys
import os
import json

# 添加api目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

def test_chinese_models_config():
    """测试国产模型配置"""
    print("=" * 50)
    print("测试国产模型配置")
    print("=" * 50)
    print()

    try:
        # 导入配置模块
        from api.config import load_json_config, CLIENT_CLASSES, CHINESE_MODELS_CONFIG

        # 测试加载国产模型配置
        print("1. 测试加载国产模型配置文件...")
        chinese_config = load_json_config("chinese_models.json")

        if chinese_config and "providers" in chinese_config:
            print("✅ 成功加载国产模型配置")
            print(f"   支持的提供商数量: {len(chinese_config['providers'])}")

            for provider_id, config in chinese_config['providers'].items():
                provider_name = config.get('provider_name', provider_id)
                default_model = config.get('default_model', 'N/A')
                models_count = len(config.get('models', {}))
                print(f"   - {provider_name} ({provider_id}): {models_count} 个模型, 默认: {default_model}")
        else:
            print("❌ 无法加载国产模型配置")
            return False

        print("\n2. 测试客户端类映射...")
        if "ChineseModelsClient" in CLIENT_CLASSES:
            print("✅ ChineseModelsClient 已注册")
        else:
            print("❌ ChineseModelsClient 未注册")
            return False

        print("\n3. 测试模型配置详情...")
        if 'CHINESE_MODELS_CONFIG' in globals():
            config = CHINESE_MODELS_CONFIG
            print("✅ CHINESE_MODELS_CONFIG 可用")
            print(f"   支持的提供商: {list(config.keys())}")
        else:
            print("❌ CHINESE_MODELS_CONFIG 不可用")
            return False

        return True

    except ImportError as e:
        print(f"❌ 导入错误: {str(e)}")
        print("   请确保在项目根目录运行此脚本，并且API模块可访问")
        return False
    except Exception as e:
        print(f"❌ 配置测试失败: {str(e)}")
        return False

def test_chinese_models_client():
    """测试国产模型客户端"""
    print("=" * 50)
    print("测试国产模型客户端")
    print("=" * 50)
    print()

    try:
        from api.chinese_models_client import ChineseModelsClient, CHINESE_MODELS_CONFIG

        print("1. 测试客户端类导入...")
        print("✅ ChineseModelsClient 导入成功")

        print("\n2. 测试模型配置数据...")
        print(f"   支持的提供商: {list(CHINESE_MODELS_CONFIG.keys())}")

        print("\n3. 测试提供商配置详情...")
        for provider_id, config in CHINESE_MODELS_CONFIG.items():
            provider_name = config['name']
            models = list(config['models'].keys())
            print(f"   {provider_name} ({provider_id}):")
            for model_id in models:
                model_info = config['models'][model_id]
                context_length = model_info.get('context_length', 'N/A')
                description = model_info.get('description', 'N/A')
                print(f"     - {model_id}: {description} (上下文: {context_length})")

        print("\n4. 测试客户端实例化...")
        # 注意：这里会因为没有API密钥而失败，这是正常的
        try:
            # 测试智谱AI客户端（如果配置了API密钥）
            if os.environ.get('ZHIPUAI_API_KEY'):
                client = ChineseModelsClient("zhipuai")
                print("✅ 智谱AI客户端实例化成功")
            else:
                print("⚠️  未配置智谱AI API密钥，跳过客户端实例化")
        except Exception as e:
            print(f"⚠️  智谱AI客户端实例化失败（预期行为）: {str(e)}")

        return True

    except ImportError as e:
        print(f"❌ 导入错误: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 客户端测试失败: {str(e)}")
        return False

def test_zhipuai_client():
    """测试智谱AI客户端"""
    print("=" * 50)
    print("测试智谱AI (GLM-4.6) 客户端")
    print("=" * 50)
    print()

    try:
        from api.zhipuai_client import ZhipuAIClient, ZHIPUAI_MODELS

        print("1. 测试ZhipuAIClient导入...")
        print("✅ ZhipuAIClient 导入成功")

        print("\n2. 测试支持的模型配置...")
        print(f"   支持的GLM模型: {list(ZHIPUAI_MODELS.keys())}")

        print("\n3. 模型详情:")
        for model_id, config in ZHIPUAI_MODELS.items():
            description = config.get('description', 'N/A')
            context_length = config.get('context_length', 'N/A')
            pricing = config.get('pricing', {})
            input_price = pricing.get('input', 'N/A')
            output_price = pricing.get('output', 'N/A')
            print(f"   - {model_id}:")
            print(f"     描述: {description}")
            print(f"     上下文长度: {context_length}")
            print(f"     价格 (输入/输出): {input_price}/{output_price} 美元/千token")

        print("\n4. 测试客户端实例化...")
        if os.environ.get('ZHIPUAI_API_KEY'):
            try:
                client = ZhipuAIClient()
                print("✅ ZhipuAIClient 实例化成功")
                print(f"   API密钥前缀: {os.environ.get('ZHIPUAI_API_KEY', '')[:10]}...")
            except Exception as e:
                print(f"⚠️  ZhipuAIClient 实例化失败: {str(e)}")
        else:
            print("⚠️  未配置ZHIPUAI_API_KEY环境变量")
            print("   要测试完整功能，请设置: export ZHIPUAI_API_KEY=your_api_key_here")

        return True

    except ImportError as e:
        print(f"❌ 导入错误: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 智谱AI客户端测试失败: {str(e)}")
        return False

def test_deepseek_client():
    """测试DeepSeek客户端"""
    print("=" * 50)
    print("测试DeepSeek客户端")
    print("=" * 50)
    print()

    try:
        from api.deepseek_client import DeepSeekClient, DEEPSEEK_MODELS

        print("1. 测试DeepSeekClient导入...")
        print("✅ DeepSeekClient 导入成功")

        print("\n2. 测试支持的模型配置...")
        print(f"   支持的DeepSeek模型: {list(DEEPSEEK_MODELS.keys())}")

        print("\n3. 模型详情:")
        for model_id, config in DEEPSEEK_MODELS.items():
            description = config.get('description', 'N/A')
            context_length = config.get('context_length', 'N/A')
            pricing = config.get('pricing', {})
            input_price = pricing.get('input', 'N/A')
            output_price = pricing.get('output', 'N/A')
            print(f"   - {model_id}:")
            print(f"     描述: {description}")
            print(f"     上下文长度: {context_length}")
            print(f"     价格 (输入/输出): {input_price}/{output_price} 美元/百万token")

        print("\n4. 测试客户端实例化...")
        if os.environ.get('DEEPSEEK_API_KEY'):
            try:
                client = DeepSeekClient()
                print("✅ DeepSeekClient 实例化成功")
                print(f"   API密钥前缀: {os.environ.get('DEEPSEEK_API_KEY', '')[:10]}...")
            except Exception as e:
                print(f"⚠️  DeepSeekClient 实例化失败: {str(e)}")
        else:
            print("⚠️  未配置DEEPSEEK_API_KEY环境变量")
            print("   要测试完整功能，请设置: export DEEPSEEK_API_KEY=your_api_key_here")

        return True

    except ImportError as e:
        print(f"❌ 导入错误: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ DeepSeek客户端测试失败: {str(e)}")
        return False

def test_environment_variables():
    """测试环境变量配置"""
    print("=" * 50)
    print("测试环境变量配置")
    print("=" * 50)
    print()

    # 测试相关的环境变量
    env_vars = {
        'ZHIPUAI_API_KEY': '智谱AI API密钥',
        'DEEPSEEK_API_KEY': 'DeepSeek API密钥',
        'DASHSCOPE_API_KEY': '阿里云通义千问API密钥',
        'MOONSHOT_API_KEY': '月之暗面API密钥',
        'WENXIN_API_KEY': '百度文心一言API密钥',
        'LINGYI_API_KEY': '零一万物API密钥',
        'MINIMAX_API_KEY': 'MiniMax API密钥',
        'DOUBAO_API_KEY': '字节跳动豆包API密钥',
        'STEPFUN_API_KEY': '阶跃星辰API密钥',
        'XUNFEI_API_KEY': '科大讯飞API密钥',
        'ENABLE_CHINESE_MODELS': '启用国产模型配置'
    }

    print("环境变量状态:")
    configured_count = 0
    for var_name, description in env_vars.items():
        value = os.environ.get(var_name)
        if value:
            configured_count += 1
            # 只显示前几个字符，保护隐私
            display_value = value[:6] + "..." if len(value) > 6 else value
            print(f"   ✅ {var_name}: {display_value} ({description})")
        else:
            print(f"   ❌ {var_name}: 未设置 ({description})")

    print(f"\n配置状态: {configured_count}/{len(env_vars)} 个变量已设置")

    if configured_count == 0:
        print("\n💡 要使用国产模型，请设置相应的API密钥:")
        print("   export ZHIPUAI_API_KEY=your_zhipuai_api_key")
        print("   export DEEPSEEK_API_KEY=your_deepseek_api_key")
        print("   export ENABLE_CHINESE_MODELS=true")
        print("\n或复制 .env.example 为 .env 并填入API密钥")

    return configured_count > 0

def main():
    """主测试函数"""
    print("DeepWiki-Open 国产模型集成测试")
    print("此测试验证国产模型的配置和基本功能")
    print()

    # 运行所有测试
    tests = [
        ("配置测试", test_chinese_models_config),
        ("通用客户端测试", test_chinese_models_client),
        ("智谱AI (GLM-4.6) 测试", test_zhipuai_client),
        ("DeepSeek 测试", test_deepseek_client),
        ("环境变量测试", test_environment_variables),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} 执行失败: {str(e)}")
            results.append((test_name, False))

    # 总结
    print("\n" + "=" * 50)
    print("测试总结")
    print("=" * 50)

    passed_count = sum(1 for _, success in results if success)
    total_count = len(results)

    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name}: {status}")

    print(f"\n总体结果: {passed_count}/{total_count} 个测试通过")

    if passed_count == total_count:
        print("🎉 所有测试通过！国产模型集成配置正确。")
        print("\n下一步:")
        print("1. 设置相应的API密钥环境变量")
        print("2. 启用国产模型配置: export ENABLE_CHINESE_MODELS=true")
        print("3. 重启后端服务: python -m api.main")
    else:
        print("⚠️  部分测试失败，请检查错误信息并修复。")

if __name__ == "__main__":
    main()