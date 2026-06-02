"""Logger, 主要由 DeepSeek 生成"""

import datetime
import glob
import logging
import os
import zipfile

import colorlog


class _FileFormatter(logging.Formatter):
    """自定义文件格式化器，在时间末尾追加毫秒"""

    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        if datefmt:
            base_time = datetime.datetime(*ct[:6]).strftime(datefmt)
        else:
            base_time = datetime.datetime(*ct[:6]).strftime("%Y-%m-%d %H:%M:%S")
        return f"{base_time}.{int(record.msecs):03d}"


def _archive_old_log(log_dir: str, log_filename: str):
    """
    将上一次运行留下的 program.log 压缩为 program-{date}-{times}.zip。
    date 取自日志文件的修改时间，times 为当天序号（自动递增）。
    """
    log_path = os.path.join(log_dir, log_filename)
    if not os.path.isfile(log_path):
        return

    # 以文件修改时间作为日志产生的日期
    mtime = os.path.getmtime(log_path)
    date_str = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")

    # 查找同一天已有的压缩包，确定序号
    pattern = os.path.join(log_dir, f"program-{date_str}-*.zip")
    existing = glob.glob(pattern)
    max_idx = 0
    for path in existing:
        name = os.path.splitext(os.path.basename(path))[0]  # program-{date}-{idx}
        parts = name.split("-")
        if len(parts) >= 4 and parts[-1].isdigit():
            idx = int(parts[-1])
            if idx > max_idx:
                max_idx = idx
    times = max_idx + 1

    zip_filename = f"program-{date_str}-{times}.zip"
    zip_path = os.path.join(log_dir, zip_filename)

    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(log_path, arcname=log_filename)
        os.remove(log_path)  # 压缩成功后删除原文件
    except Exception as e:
        print(f"归档旧日志失败: {e}")


_configured = False


def setup_logging(log_dir: str = "logs",
                  log_filename: str = "program.log",
                  console_level: int = logging.INFO,
                  file_level: int = logging.DEBUG,
                  ):
    """
    配置全局日志系统（仅首次调用有效）。
    控制台输出格式：[HH:MM] [ThreadName/LEVEL] [filename]: message
    文件输出格式：  [YYYY-MM-DD HH:MM:SS.ms] [ThreadName/LEVEL] [filename(funcName)]: message
    """
    global _configured
    if _configured:
        return

    os.makedirs(log_dir, exist_ok=True)
    _archive_old_log(log_dir, log_filename)

    # 根 Logger 设为最低级别，由 Handler 各自控制
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.handlers.clear()

    # --- 控制台 Handler（带颜色）---
    console_fmt = colorlog.ColoredFormatter(
        "[%(asctime)s] [%(threadName)s/%(log_color)s%(levelname)s%(reset)s] [%(filename)s]: %(message)s",
        datefmt="%H:%M",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
    )
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(console_fmt)
    root.addHandler(console_handler)

    # --- 文件 Handler（带毫秒）---
    file_fmt = _FileFormatter(
        "[%(asctime)s] [%(threadName)s/%(levelname)s] [%(filename)s(%(funcName)s)]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler = logging.FileHandler(
        os.path.join(log_dir, log_filename), mode="w", encoding="utf-8",
    )
    file_handler.setLevel(file_level)
    file_handler.setFormatter(file_fmt)
    root.addHandler(file_handler)

    _configured = True


def get_logger() -> logging.Logger:
    """
    获取已配置好格式的 Logger。
    首次调用会自动初始化日志系统（setup_logging）。
    """
    setup_logging()
    return logging.getLogger()


logger = get_logger()
debug = logger.debug
info = logger.info
warning = logger.warning
error = logger.error
critical = logger.critical
exception = logger.exception

# # ============ 使用示例 ============
# if __name__ == "__main__":
#     logger = get_logger(__name__)
#     logger.debug("这是一条 DEBUG 日志（仅文件）")
#     logger.info("HelloWorld")
#     logger.warning("警告信息")
#     logger.error("错误信息")
#     logger.critical("严重错误")
