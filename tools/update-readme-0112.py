"""Update README/report for 0.1.12: gallery aligned with the original CG list."""
from pathlib import Path

p = Path(r'D:\DSH\work\port\senren-rw5\README.md')
t = p.read_text('utf8')
t = t.replace('移植版 0.1.11', '移植版 0.1.12')
t = t.replace('**24,350,321 字节**', '**24,350,737 字节**')
t = t.replace('0.1.11 / versionCode 12', '0.1.12 / versionCode 13')
t = t.replace('| CG 差分图 | 634 | 1,481 |', '| CG 差分图 | 634 | 1,479 |')

t = t.replace('''设备实测：官方模拟器的安装器在 **4,156 个条目**时能装、**4,177 个条目**时报 `rpkpackage -19`（解包时 `mkfile/write` 失败）。''',
'''## 图库对齐

`src/common/gallery.txt` 现在直接按原作的 CG 模式清单生成：基础版 `data/main/cglist.csv`（78 组）+ 成人补丁 `cglist_0.csv`（45 组），
分组顺序、组名（芳01…茉04…芦03…）和组内差分顺序都跟原作一致。原作清单共列 3,758 个差分名，
本移植版只转换了其中 1,479 个（其余是同一图组的其它姿态/表情变体），缺失的按顺序跳过，不重排。

结果：本次 122 组 / 1,479 张，`茉04` 的首图是正片 CG（ev204ab），不再是此前被放到首位的 `ev204_aa`。
`ev204_aa` 确实存在于原作：它是 `cglist.csv` 里 `茉04` 组的一个差分（`ev204_aa`，末位），
也是成人脚本 `203・茉子－子犬` 第 247 帧起的回想插入图（基础版同一帧只有黑屏）。

## 安装问题与处理（官方模拟器实测）

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| `Failed to deal with rpkpackage -19` | 解包阶段 `app_verify.c` 的 `mkfile`/`write` 失败 | 见下面两条 |
| 同上，包体并不大 | 安装器按**条目数**限制：4,156 条能装、4,177 条失败 | 把故事块上限 24 → 28 KiB，块数 914 → 815，条目降到 4,068 |
| 同上，首次安装 | `/data` 只有 255 MB，旧版已装时剩余不足 | 先 `pm uninstall` 旧版再装（存量存档在应用数据里，卸载后槽位仍在） |
| 安装成功后界面报「!」占位、图片打不开 | 旧进程还在跑，引用的是上一版的文件名 | `am stop` 后重新 `/start`，再看界面 |
| `-2 Not found package` | 卸载一个本来就没装的包 | 忽略，继续安装 |

��备实测：官方模拟器的安装器在 **4,156 个条目**时能装、**4,177 个条目**时报 `rpkpackage -19`（解包时 `mkfile/write` 失败）。''')
p.write_text(t, 'utf8')
print('ok', len(t))
