# MAA 项目长期记忆

## 项目概况

- MaaFramework 自动化项目（抖音商城比价/代付/好评），基于 maa-tools 模板
- 开发布局：interface.json 在 `assets/`，pipeline 在 `assets/resource/pipeline/`，Python agent 在根目录 `agent/`
- 调试方式：VS Code 插件（nekosu.maa-support）+ MPE FlowScope

## 关键环境事实

- MaaFramework Python binding（maa 包）装在 `C:\Users\StellarAI\AppData\Local\Python\pythoncore-3.14-64\python.exe`；系统 `python`(3.13) 没有装
- interface.json 的 agent.child_exec 已指向上述 3.14 python；child_args 为 `../agent/main.py`（CWD=assets/）
- agent 子进程 CWD = interface.json 所在目录（Project Interface V2 规范）

## 打包注意

`tools/install.py` 会摊平布局（interface.json、agent/ 同级放到 install/）。**install.py 已在 install_resource() 里实现：**
- 打包时把 child_args 的 `../agent/main.py` 自动改写为 `agent/main.py`
- 打包时把 `assets/logo.ico` 复制到 `install/logo.ico`（interface.json 已加 `"icon": "logo.ico"`）

图标机制（参考 M9A）：exe 不嵌入图标，logo.ico 是独立文件由 GUI（MFAAvalonia/MaaPiCli）运行时读取；替换 assets/logo.ico 即换图标。完整打包需要 deps/ 下有 MaaFramework 运行时（deps/bin 当前不存在，尚未下载）。

## agent 架构（2026-09-01 定稿）

- `agent/main.py`：入口，socket_id + AgentServer.join()，import agent_table 触发注册
- `agent/agent_table.py`：注册自定义动作 "ProcessReview"，查 agent/reviews.csv（UTF-8，列：订单编号/评价内容/图片路径）
- pipeline 评价.json 的"检测编号_查表"节点引用 ProcessReview

## 遗留事项

- interface.json 任务「4. 自动好评」入口是空节点"好评入口节点"，未连接评价.json 实际流程
- reviews.csv 图片路径列全为空，ProcessReview 的 adb 推图分支暂不生效
- 参考范本：D:\MAA\M9A-win-x86_64-v4.6.2-MFAA（发布包扁平布局）
