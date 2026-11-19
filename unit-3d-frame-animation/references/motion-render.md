# 动作与渲染

## 片段与时序

动作清单写源名称、片段起止及端点语义、fps、源范围、采样映射、是否循环、一次总时长。Action有同名关键帧不代表动作正确；检查动画槽、NLA、约束与默认通道。重置通道的项目方式明确后使用，不任意清除驱动/约束。整段源范围不一定是实际片段。

循环展示完整双腿周期，不保留重复边界帧；边界额外评估但不交付。Idle看落脚稳定和呼吸，Move看双腿、支撑和循环，Attack看准备/发射姿态/后坐/恢复。Walk不改名冒充Run。来源有循环错位先披露，修复需相应授权，不用插帧/混合掩盖。

保留原fps和时长。采样减帧需同时保留总时长与关键姿态，不能只减duration。一次性攻击完整播完后保持或留白；预览合集重复播放须说明是审核回放，非实际连续攻击规则。给原速MP4、原尺寸与倍率放大，必要时联系表和脚部轨迹。

## 原生Blender批量工具

在已批准blend上先确认渲染器、材质、透明Film、色彩管理、源相机和骨骼动作可独立重开。脚本不替代这些操作。

调用：`blender -b -t 6 --python <skill>/scripts/render_blender.py -- --config <run.json>`。工具版本和线程数由当前环境确定。

配置UTF-8 JSON，路径相对配置文件目录解析；以下仅字段示例，不是固定角色数值：

```json
{
  "blend": "source.blend",
  "output": "delivery/Unit",
  "work": "work/raw",
  "armature": "Armature",
  "reset_action": "Armature_DEFAULTS",
  "reset_frame": 0,
  "canvas": [112,112],
  "supersample": 4,
  "outline_px": 1,
  "fps": 30,
  "samples": 16,
  "pivot": {"x":0.5,"y":0.25},
  "directions": {"UpRight":"Game_UpRight","DownRight":"Game_DownRight"},
  "actions": [{"name":"Idle","source":"Armature_Stand_full","frames":[0,1,2],"duration_ms":100,"loop":true}]
}
```

`frames`必须是已经确认的明确采样列表，可带子帧；默认动作必须存在。脚本验证正交相机共用尺度和输出目录未存在，源blend不写回；保留完整原始渲染和运行清单到work。当前工具针对单骨架Action、正交相机、Cycles渲染，可选Blender动画槽；NLA混合、多骨架同步、约束驱动片段需专门适配并验证，不通过脚本成功声称支持。源场景必须自行准备完毕；工具不生成/禁用灯光或修改材质。

超采样后用原生合成器缩小，再按最终像素膨胀Alpha叠黑底描边。描边仅改变输出，不写入源材质。首次用小范围试渲染，检查色彩、透明、轮廓、落脚点后再全量运行。失败输出不原地重试覆盖，先检查完成记录并另建候选，避免残帧混入。

## 验收证据

逐帧技术检查全部图片；联系表看网格完整、关节、装饰稳定、裁切和Alpha；原速视频看连续性、金属跳变和小尺寸辨识。材质修改时比较几何/Action摘要与已批准源，不能只检查PNG尺寸。跨动作原尺寸Idle→Move→Attack→Idle及镜像转向是独立审核项。
