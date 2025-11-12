#!/bin/bash

# Claude Code 环境变量配置脚本
# 使用方法：source ./setup-env.sh 或 . ./setup-env.sh

# 检查脚本是否被 source 执行
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "错误：此脚本必须通过 source 命令执行"
    echo "用法：source ./setup-env.sh"
    echo "或    . ./setup-env.sh"
    exit 1
fi

# 定义常量
BASE_URL="https://api.moonshot.cn/anthropic"
MODEL_OPTIONS=(
    "kimi-k2-thinking"
    "kimi-k2-0905-preview"
)

echo "======================================"
echo "  Claude Code 环境变量配置"
echo "======================================"
echo

# 设置 ANTHROPIC_AUTH_TOKEN
echo -n "请输入 ANTHROPIC_AUTH_TOKEN (密码不显示): "
read -s auth_token
echo

# 是否覆盖已存在的值
if [[ -n "$ANTHROPIC_AUTH_TOKEN" ]]; then
    echo "注意：ANTHROPIC_AUTH_TOKEN 已存在，将被覆盖"
    echo
fi

export ANTHROPIC_AUTH_TOKEN="$auth_token"

# 设置 ANTHROPIC_BASE_URL
export ANTHROPIC_BASE_URL="$BASE_URL"

# 设置 ANTHROPIC_MODEL
echo "请选择 ANTHROPIC_MODEL:"
PS3="选择数字进行选择，然后按回车: "
select model in "${MODEL_OPTIONS[@]}"; do
    if [[ -n "$model" ]]; then
        export ANTHROPIC_MODEL="$model"
        break
    fi
done
echo

# 设置 ANTHROPIC_SMALL_FAST_MODEL
echo "请选择 ANTHROPIC_SMALL_FAST_MODEL:"
PS3="选择数字进行选择，然后按回车: "
select small_fast_model in "${MODEL_OPTIONS[@]}"; do
    if [[ -n "$small_fast_model" ]]; then
        export ANTHROPIC_SMALL_FAST_MODEL="$small_fast_model"
        break
    fi
done
echo

# 验证并显示已设置的值
echo "======================================"
echo "环境变量设置成功！"
echo "======================================"
echo "ANTHROPIC_BASE_URL: $ANTHROPIC_BASE_URL"
echo "ANTHROPIC_AUTH_TOKEN: ${ANTHROPIC_AUTH_TOKEN:0:8}... (已隐藏)"
echo "ANTHROPIC_MODEL: $ANTHROPIC_MODEL"
echo "ANTHROPIC_SMALL_FAST_MODEL: $ANTHROPIC_SMALL_FAST_MODEL"
echo
echo "这些变量已在当前 Shell 会话中生效"
