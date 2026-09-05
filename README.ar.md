# lotuseater-skills

[English](README.md) | [中文](README.zh-CN.md) | العربية

مجموعة مهارات الوكلاء (Agent Skills) من Lotuseater. كل مهارة في دليل خاص بها تحت `skills/`، باتباع الهيكل المحدد في [docs/skill-spec.md](docs/skill-spec.md) (بالصينية).

## التثبيت (سوق إضافات Claude Code)

```
/plugin marketplace add HotRiceNoodles/lotuseater-skills
```

ثم ثبّت المهارات الفردية حسب الحاجة:

```
/plugin install traceable-meeting-minutes@lotuseater-skills
```

## التثبيت اليدوي (Claude Code)

بدلاً من ذلك، استنسخ المستودع ثم اربط أو انسخ دليل المهارة إلى `~/.claude/skills/`:

```bash
git clone https://github.com/HotRiceNoodles/lotuseater-skills.git
ln -s "$(pwd)/lotuseater-skills/skills/traceable-meeting-minutes" ~/.claude/skills/traceable-meeting-minutes
```

(على Windows، استخدم `mklink /D` أو انسخ الدليل.)

## المنصات الأخرى

تتبع هذه المهارات [مواصفة Agent Skills المفتوحة](https://agentskills.io/specification) (SKILL.md + ترويسة YAML) وتعمل على أي منصة وكلاء متوافقة معها. الطريقة العامة: استنسخ هذا المستودع، ثم انسخ دليل `skills/<skill-name>/` بالكامل أو اربطه بدليل المهارات في المنصة المستهدفة.

| المنصة | دليل المهارات / طريقة التثبيت |
|--------|-------------------------------|
| **Claude Code** | سوق الإضافات (انظر أعلاه)، أو `~/.claude/skills/` (على مستوى المستخدم) / `.claude/skills/` (على مستوى المشروع) |
| **Codex** | `~/.codex/skills/` (على مستوى المستخدم) أو `.codex/skills/` (على مستوى المشروع). ملاحظة: قد لا تُكتشف المهارات المرتبطة برمزية ([#9365](https://github.com/openai/codex/issues/9365)) — يُنصح بنسخ الدليل |
| **OpenClaw** | `openclaw skills install <path-or-url> [--global]`؛ الدليل العام `~/.openclaw/skills/`، أو ضع المهارة في دليل `skills/` داخل مساحة العمل |
| **Hermes Agent** | `hermes skills install <url>` أو يدويًا في `~/.hermes/skills/`. ملاحظة: قد يجلب تثبيت مهارة متعددة الملفات عبر URL ملف SKILL.md فقط ([مشكلة معروفة](https://github.com/NousResearch/hermes-agent/issues/35125)) — استنسخ المستودع وانسخ الدليل كاملًا بدلاً من ذلك |
| **QwenWork (تشيين ون**)** | `~/.qwenworkcn/skills/` |
| **Doubao (وضع مهام المكتب)** | Doubao لسطح المكتب → وضع مهام المكتب → استيراد من ساحة المهارات، أو ضع دليل المهارة في مجلد المهارات المحلي (اتبع الإرشادات داخل التطبيق) |
| **Tencent WorkBuddy** | `~/.workbuddy/skills/<skill-name>/SKILL.md` (على Windows يعمل أيضًا `%APPDATA%\WorkBuddy\skills\`)، أو الاستيراد عبر "إدارة المهارات" في العميل. يتطلب Node.js / Git / (على Windows) .NET Runtime |

مثال (Codex):

```bash
git clone https://github.com/HotRiceNoodles/lotuseater-skills.git
cp -r lotuseater-skills/skills/traceable-meeting-minutes ~/.codex/skills/
```

> جميع المهارات في هذه المجموعة مصممة لتكون مستقلة عن المنصة: تكتشف منصة الوكيل المضيف وقت التشغيل وتحفظ إعداداتها في دليل المهارة الخاص `~/.<skill-name>/`، دون الاعتماد على مسارات خاصة بمنصة معينة. للمهارات التي تتضمن سكربتات Python، ثبّت `scripts/requirements.txt` عند ظهور المطالبة عند أول استخدام.

## المهارات

| المهارة | ما تفعله |
|---------|----------|
| [traceable-meeting-minutes](skills/traceable-meeting-minutes/) | تسجيل/نص الاجتماع → محضر قابل للتتبع: سجل دلالي + ضغط تفاضلي + HTML تفاعلي (كل استنتاج يعود إلى الكلمات الأصلية ولحظة الصوت) + تدقيق "ما تم حذفه" |
| [cinematic-pptx-pipeline](skills/cinematic-pptx-pipeline/) | خط إنتاج كامل للعروض/المواد التعليمية متعدد الأنماط (سينمائي / رسم يدوي / قومي صيني / زجاجي): رسوم توضيحية بالذكاء الاصطناعي → صفحات HTML → فحص جودة بلقطات الشاشة → تسليم PPTX بثلاثة مستويات (صور نقطية / قابل للتحرير / متحرك) → فيديو MP4 |

## مواصفة المساهمة

يجب أن تتبع المهارات الجديدة [docs/skill-spec.md](docs/skill-spec.md) (بالصينية). النقاط الأساسية:

- مهارة واحدة لكل دليل (`skills/<name>/`)؛ اسم الدليل == `name` في الترويسة (kebab-case)
- SKILL.md أقل من 200 سطر، توجيه وقواعد صارمة فقط؛ التفاصيل في `workflows/` و`references/` و`templates/`
- مستقل عن المنصة: لا مفاتيح/مسارات شخصية مثبتة في الكود ولا ارتباط بمنصة معينة؛ تُعالَج فروق المنصات تلقائيًا عند أول تشغيل
- سكربتات Python تُرفق مع `scripts/requirements.txt` ورسائل خطأ ودية عند فشل الاستيراد
- اجتياز قائمة الفحص في المواصفة §7 ونجاح `claude plugin validate .` قبل الدمج

## الترخيص

[MIT](LICENSE)
