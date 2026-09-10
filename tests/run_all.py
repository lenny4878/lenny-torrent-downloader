"""Run desktop suites in isolated processes, failing immediately on any regression."""
import datetime
import subprocess
import sys
from pathlib import Path

root=Path(__file__).resolve().parents[1]
suites=['test_integration.py','test_tray.py','test_windows_identity.py','test_playback.py','test_basic_ui.py','test_i18n.py']
results=[]
for suite in suites:
    print(f'\nRunning {suite}',flush=True)
    result=subprocess.run([sys.executable,str(root/'tests'/suite)],cwd=root)
    results.append(f'- {suite}: '+('通过' if result.returncode==0 else '失败'))
    if result.returncode:
        break
passed=len(results)==len(suites) and result.returncode==0
report='# 基础功能回归\n\n运行时间：'+datetime.datetime.now().isoformat(timespec='seconds')+'\n\n'+'\n'.join(results)
report+='\n\n结果：'+('全部通过。' if passed else '未通过，后续套件未运行。')
report+='\n\n测试使用生成文件和临时目录。覆盖完整传输、Magnet 元数据、暂停/停止/重启、排队、两种删除、HTTP 分片读取、托盘、Windows 图标标识、实际部分下载视频播放、设置及文件交互。不能代替所有公网环境、编码和长期稳定性测试。\n'
(root/'docs').mkdir(exist_ok=True)
(root/'docs'/'test-report.md').write_text(report,'utf-8')
sys.exit(0 if passed else 1)
