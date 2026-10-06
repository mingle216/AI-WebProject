# MURONG 企业官网

## 项目简介

本项目是南通睦融电气设备有限公司（MURONG）的中英双语企业官网。当前处于静态页面阶段，以 `test-last.html` 为主页面，正按 [一期需求文档](docs/rongelec-phase-1-requirements.md) 推进全栈改造。

## 目录结构

- `assets/`：业务范围、配件和地图等站点素材。
- `murong-pic/`：公司相关图片与展示资料。
- `docs/`：一期需求、全栈规划及设计文档。
- `tests/`：站点内容自检脚本。
- 根目录 HTML 页面：`test-last.html` 为当前主页面，`privacy.html` 和 `terms.html` 分别为隐私政策与服务条款页；另有 `welcome-ui-preview.html` 和 `murong官网设计参考.html`。
- 根目录还存放 Logo、图片和视频等静态素材。

## 运行测试

在仓库根目录运行：

```sh
python3 tests/site_content_test.py
```

这是基于 Python 标准库 `unittest` 的站点内容自检，无需安装第三方测试依赖。

## 工单托管

开发工单走 `_tickets/` 目录管理（open/doing/done 流转），细节见 `_tickets/workers.md`。
