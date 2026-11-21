# Copy-Ready Prompt Templates (可复用 Prompt 模板)

Use **Template A** when briefing a 3D modeling agent, Blender script pipeline, or human 3D artist for a multi-asset batch. Use **Template B** when generating individual assets in single-object AI image/3D tools (Flux, Midjourney, Nano Banana, Tripo, Meshy, Rodin).

---

## Template A: Master Control Prompt (总控规范版 — 中文)

Replace all `{{...}}` placeholders with project-specific details.

```markdown
# 角色与任务
你是一位专业工业设计与技术可视化 3D 资产设计师，现需为「{{项目名称与应用场景，如：新能源微网教学套件 / 医疗诊断设备路演}}」制作一套视觉高度统一、结构严谨的 3D 剖面与硬件道具资产（共 {{N}} 组）。

# 全局视觉与技术规范（所有资产必须严格统一）
1. **美术风格**：Precision Industrial Hard-Surface & Technical Cutaway（写实工业硬表面精模与工程剖面），干净的几何倒角、结构加强筋、法兰螺栓、标准化接插件与规整布线；拒绝低幼卡通、拒绝廉价赛博霓虹光污染、拒绝杂乱装饰。
2. **统一材质与色板（适配深空暗底 `#060E1A` 与白色文档纸面双场景）**：
   - 中性基底（占 75%–85%）：
     - 主外壳米白搪瓷：`#D3CFBC` / `#E1E0CC`（避免死白）
     - 结构钛合金 / 拉丝铝：`#ADB7B8` / `#93A2A3`
     - 阳极氧化深灰底板 / 散热片 / 机架：`#353F45` / `#2B353B`
     - 镀金触点 / 铜质热端或管件：`#D9A74A`
   - 语义功能色（占 15%–25%，单件不超过 3 种）：
     - 翡翠绿（{{定义语义：如核心保底 / 主母线 / 正常在线}}）：`#34D399`
     - 工业青蓝（{{定义语义：如数据遥测 / 水路 / 冷端 / 轮廓光}}）：`#48CAE4` / `#509A95`
     - 暖琥珀橙（{{定义语义：如热端防护 / 可调度负荷 / 警示点缀}}）：`#FF8F45` / `#DF9B47`
3. **统一相机与布光**：
   - 机位：3/4 等轴微俯视（俯角锁定 `27°`，范围 `25°–30°`，等效焦距 `55–65 mm` 控畸变）；
   - 布光：左前上方暖白柔光主光 + 右后侧清晰的冷青色（`#48CAE4`）轮廓边缘光 + 柔和内部补光，确保深灰金属件在暗背景下边缘分明；
   - **严禁烘焙任何文字、数字、乱码标签、Logo 水印或悬浮 HUD**（所有仪器屏幕保持干净的空白暗色 OLED 玻璃屏）。
4. **交付格式与命名（输出至 `{{目标目录}}`）**：
   - 必交：**透明背景 RGBA PNG**（`2400 × 1600 px`，无背景色块、无生硬方形裁切阴影，四边至少保留 `5%` 透明边距）；
   - 选交/推荐：**分层命名 `.glb`**（外壳、内部组件、灯组、接口独立分层，右手系 `+Y` 朝上，居中于原点）；
   - **锁机位要求**：凡标明「对比组 / 双态」的资产，必须锁死完全一致的相机参数与底板位置出图。

# 资产清单与具体建模规格

## [P0-1] {{资产名称}}（{{单态 / 锁机位双态}}）
- **文件命名**：`{{snake_case_name}}.png` / `.glb`
- **原型分类**：{{物理剖面 / 锁机位双态 / 桌面模块化教具 / 地质工艺断面 / 极简沙盘}}
- **结构与微细节要求**：
  - 外框与底座：{{描述切角底座 / 外壳结构肋 / 剖开 110°–135° 双层壳壁厚度}}
  - 核心内部件与比例：{{按左/中/右或底/中/顶分层描述，如有数据比例明确写出如 3:7}}
  - 接口与状态差异：{{描述热插拔悬浮 15mm / 镀金弹簧针 / 不对称定位销 / 双态灯光或结构变化}}
- **领域红线（严禁穿帮）**：{{写出 1–2 条该领域的物理/安全/科学禁止项，例如无明火、无 220V 市电插头、无文字标签}}
```

---

## Template B: Standalone Single-Asset Prompt Formula (单件出图英文公式)

Designed for Flux, Midjourney, Nano Banana, Tripo, Meshy, and Rodin. Follow this exact 6-slot order so model attention stays locked on geometry and style:

```text
[1. Framing & Archetype]
Isometric 3/4 {{studio technical render / engineering cutaway / geological cylinder cutaway diorama / architectural scale-model diorama}} of {{SUBJECT}} resting on {{a matte dark-grey chamfered lab baseplate / a chamfered light-grey display plinth}}:

[2. Exterior Silhouette & Sectioning]
{{Exterior shell material — e.g., off-white enamel (#D3CFBC) housing with brushed titanium reinforcement ribs}}, {{optional: front 120-degree wall cleanly sectioned open revealing thick double-wall insulation and neat interior bay}};

[3. Ordered Interior / Hardware Anatomy]
{{Describe spatially left-to-right or bottom-to-top using concrete mechanical nouns — modular racks, gold pogo-pin contacts, asymmetric alignment keys, tidy orthogonal color-coded pipes/cables, blank dark OLED glass display}};

[4. Semantic Color Coding (<= 3 Accents)]
{{Explicitly assign emerald-green (#34D399), industrial cyan (#48CAE4), and/or warm amber (#FF8F45) accents to functional parts}};

[5. Style, Camera & Studio Lighting Lock]
Precision aerospace industrial hard-surface design, clean geometric chamfers, 27-degree elevated isometric view, 60mm lens, warm-white studio key light from top-left, crisp cyan (#48CAE4) rim light from back-right, clean matte and brushed metallic materials;

[6. Output Isolation & Negative Guardrails]
isolated on transparent background, generous 5% clean margin on all sides, {{domain safety guardrails — e.g., safe low-voltage DC design, no open flame, no AC wall plugs, no exhaust smoke}}, no text, no letters, no numbers, no gibberish labels, no HUD, no watermark.
```

> **Fallback for tools without native alpha transparency**: Replace `isolated on transparent background` with `isolated on solid uniform dark navy background #060E1A` (for dark-deck projects) or `isolated on solid uniform neutral light grey background #F4F7FA` (for light-only print projects), then extract cleanly in post-processing.

---

## Template C: Locked-Camera State B Follow-Up Prompt (双态对比图生图模板)

When producing State B from State A via image-to-image / edit models:

```text
Same exact isometric 3/4 camera angle, lighting rig, framing, and {{SUBJECT}} architecture as the reference image, with zero shift in horizon or plinth edges. Change ONLY {{EXACT VARIABLE — e.g., switch off half of the overhead linear LED bars and dim the interior lighting to low-power preservation mode / lift the fourth amber modular cube 15mm vertically above its socket to reveal the 8 gold pogo-pins and two asymmetric alignment keys underneath}}. Keep all other materials, structural ribs, and colors identical. Isolated on transparent background, no text, no labels, no watermark.
```
