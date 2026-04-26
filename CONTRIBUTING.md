# Contributing to Heard

感谢你对 Heard 感兴趣！欢迎提交 Issue 和 Pull Request。

## 开发环境设置

```bash
git clone https://github.com/xiaoqianghan/heard.git
cd heard
uv sync
```

系统需要安装 FFmpeg：`brew install ffmpeg`（macOS）

## 开发流程

1. Fork 本仓库
2. 从 `main` 创建功能分支：`git checkout -b feature/your-feature`
3. 编写代码和测试
4. 确保所有测试通过：`uv run pytest -v`
5. 提交 PR，描述清楚改动内容和动机

## 代码规范

- 用 `uv` 管理依赖，不直接修改 `uv.lock`
- 新功能必须有对应测试（`tests/test_*.py`）
- 遵循现有代码风格
- 提交信息用英文，简洁明了

## 报告 Bug

请提交 [GitHub Issue](https://github.com/xiaoqianghan/heard/issues)，包含：

- 操作系统和 Python 版本
- 复现步骤
- 期望行为 vs 实际行为
- 相关日志或错误信息

## License

提交代码即表示你同意以 MIT 许可证贡献你的改动。
