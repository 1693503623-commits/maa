import csv
import difflib
import os
import re
import subprocess
import traceback
from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context

# 定位脚本所在目录（agent/），表格就放在同一目录
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(AGENT_DIR)
CSV_PATH = os.path.join(AGENT_DIR, "reviews.csv")

# 预加载 CSV 数据（utf-8-sig 兼容带 BOM 的 Excel 导出文件）
review_data = {}
try:
    with open(CSV_PATH, mode="r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            review_data[row["订单编号"].strip()] = {
                "text": row.get("评价内容") or "",
                "image": (row.get("图片路径") or "").strip(),
            }
    print(f"[agent_table] 成功加载评价表，共 {len(review_data)} 条，路径：{CSV_PATH}")
except Exception as e:
    print(f"[agent_table] 表格读取失败: {e}")
    print(traceback.format_exc())


def _get_all_ocr_texts(reco_detail) -> list[str]:
    """把识别区所有 OCR 结果文本都收进来（不止 best_result），供后续抽订单号"""
    texts: list[str] = []
    candidates = []
    best = getattr(reco_detail, "best_result", None)
    if best is not None:
        candidates.append(best)
    filtered = getattr(reco_detail, "filtered_results", None) or []
    all_res = getattr(reco_detail, "all_results", None) or []
    for res in list(filtered) + list(all_res):
        if res not in candidates:
            candidates.append(res)
    for res in candidates:
        t = getattr(res, "text", None)
        if t:
            texts.append(str(t))
    return texts


def _extract_order_ids(texts: list[str]) -> list[str]:
    """从 OCR 文本中抽取订单号（19 位连续数字），按出现顺序去重返回。

    自动剥离"复制"等杂字：例如 "6955496919031617290复制" 只会抽到 19 位纯数字。
    """
    ids: list[str] = []
    for t in texts:
        for token in re.findall(r"\d{19}", t):
            if token not in ids:
                ids.append(token)
    return ids


def _get_ocr_text(reco_detail) -> str:
    """从识别结果中提取 OCR 文本（reco_detail 本身没有 .text 字段）"""
    best = getattr(reco_detail, "best_result", None)
    if best is not None:
        return getattr(best, "text", "") or ""
    filtered = getattr(reco_detail, "filtered_results", None)
    if filtered:
        return getattr(filtered[0], "text", "") or ""
    return ""


@AgentServer.custom_action("ProcessReview")
class ProcessReviewAction(CustomAction):

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        try:
            return self._run(context, argv)
        except Exception:
            # 最外层兜底：任何异常都必须打印出来，避免哑火返回 False
            print("[ProcessReview] 动作抛出异常，详见下方 Traceback：")
            print(traceback.format_exc())
            return False

    def _run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        # 1. 收集识别区所有 OCR 文本
        texts = _get_all_ocr_texts(argv.reco_detail)
        ocr_text = _get_ocr_text(argv.reco_detail)
        print(f"[ProcessReview] OCR 原文: {ocr_text}")

        # 2. 抽取所有可能的订单号（19 位纯数字，自动过滤"复制"等杂字）
        order_ids = _extract_order_ids(texts)
        print(f"[ProcessReview] 识别到的候选订单号: {order_ids}")

        # 3. 命中一个即可
        order_id = None
        if order_ids:
            for oid in order_ids:
                if oid in review_data:
                    order_id = oid
                    break
            # 都不在表里：优先用第一个候选，方便用户比对
            if order_id is None:
                order_id = order_ids[0]

        if order_id is None or order_id not in review_data:
            if order_id is None:
                print(f"❌ 提取失败，未找到19位单号: {ocr_text}")
            else:
                print(f"❌ 查无此单: {order_id}")
                # 打印 CSV 里最相似的订单号，方便判断是 OCR 识别错还是号本身不对
                similar = difflib.get_close_matches(
                    order_id, review_data.keys(), n=3, cutoff=0.6
                )
                print(f"[ProcessReview] CSV 中最相似的订单号: {similar}")
            return False

        data = review_data[order_id]
        print(f"[ProcessReview] 命中订单: {order_id}")

        # 4. 覆盖下一个节点的输入文本参数
        context.override_pipeline(
            {
                "点击输入框并填入文本": {
                    "action": {
                        "param": {
                            "input_text": data["text"],
                        }
                    }
                }
            }
        )

        # 5. 如表格里配了图片路径，则推送到手机相册；没配就跳过
        if data["image"]:
            img_abs_path = os.path.join(PROJECT_ROOT, "assets", "resource", data["image"])
            if os.path.exists(img_abs_path):
                subprocess.run(
                    f'adb push "{img_abs_path}" /sdcard/DCIM/Camera/MaaReview.jpg',
                    shell=True,
                )
                subprocess.run(
                    "adb shell am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE"
                    " -d file:///sdcard/DCIM/Camera/MaaReview.jpg",
                    shell=True,
                )
            else:
                print(f"[ProcessReview] 图片不存在，跳过推送: {img_abs_path}")
        else:
            print("[ProcessReview] 表格未配置图片路径，跳过推送")

        return True
