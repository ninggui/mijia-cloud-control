#!/opt/data/mijia_venv/bin/python
"""灯光节奏律动模板：按旋律序列控制米家灯开关，时值对比出律动。

用法：改 DID（目标灯）、ON/ON_LONG/GAP/PHRASE_PAUSE（时值）、rows（旋律序列）后运行。
原理：云端 miotspec/prop/set 延迟 ~150ms，拍子 >=0.5s 才稳；律动 = 短音/长音/乐句停顿对比。
注意：串行调用；try/finally 兜底关灯；多灯同步也循环串行。
"""
import sys, time
sys.path.insert(0, '/opt/data/skills/@clawhub_lanlan314/xiaomi-miot-lan')
from mijia_api import MijiaCloud

DID = '<DID>'          # 阳台灯（领普单键开关，蓝牙mesh，A房）
ON = 0.66                  # 普通音亮秒（BPM90 一拍）
ON_LONG = 1.32             # 延音亮秒（两拍）
GAP = 0.25                 # 音符间灭秒
PHRASE_PAUSE = 1.2         # 乐句间停顿秒
# 小星星 简谱：数字=do/re/mi...，'-'=延音（2拍）；每行一个乐句
rows = [
    [1, 1, 5, 5, 6, 6, 5, '-'],
    [4, 4, 3, 3, 2, 2, 1, '-'],
    [5, 5, 4, 4, 3, 3, 2, '-'],
    [5, 5, 4, 4, 3, 3, 2, '-'],
]

mc = MijiaCloud()


def flash(dur):
    mc.api('/miotspec/prop/set', {'params': [{'did': DID, 'siid': 2, 'piid': 1, 'value': True}]})
    time.sleep(dur)
    mc.api('/miotspec/prop/set', {'params': [{'did': DID, 'siid': 2, 'piid': 1, 'value': False}]})


try:
    for row in rows:
        for j, n in enumerate(row):
            flash(ON_LONG if n == '-' else ON)
            time.sleep(PHRASE_PAUSE if j == len(row) - 1 else GAP)
        print('phrase done', flush=True)
finally:
    mc.api('/miotspec/prop/set', {'params': [{'did': DID, 'siid': 2, 'piid': 1, 'value': False}]})
    print('finished, light off', flush=True)
