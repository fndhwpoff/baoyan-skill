/**
 * question_loader.js
 * 从后端 API 加载面试题，支持中英文模式切换，含内置示例题目。
 */

const QuestionLoader = (() => {
    // 内置英文示例题目（API 不可用时使用）
    const FALLBACK_QUESTIONS_EN = [
        {
            id: "en001",
            question: "Please introduce yourself and explain why you want to pursue a graduate degree in mechanical engineering.",
            category: "general",
            hint: "Keep it under 2 minutes. Cover: who you are, your major, your research interests, and why grad school.",
            language: "en",
        },
        {
            id: "en002",
            question: "Tell me about your most significant research project or technical experience. What was YOUR specific contribution?",
            category: "technical",
            hint: "Use the STAR method: Situation, Task, Action, Result. Emphasize what YOU did, not the team.",
            language: "en",
        },
        {
            id: "en003",
            question: "Describe a time when you faced a major technical challenge or experimental failure. How did you handle it?",
            category: "behavioral",
            hint: "Show resilience and problem-solving. What did you learn? What would you do differently?",
            language: "en",
        },
        {
            id: "en004",
            question: "Why did you choose our program? Which faculty members' research are you interested in?",
            category: "general",
            hint: "Do your homework. Mention specific professors and their recent work.",
            language: "en",
        },
        {
            id: "en005",
            question: "Can you explain the concept of Finite Element Analysis to someone without an engineering background?",
            category: "technical",
            hint: "Start with a simple analogy. Focus on the 'why' and 'when', not just the 'what'.",
            language: "en",
        },
        {
            id: "en006",
            question: "Tell me about a situation where you had to collaborate with difficult teammates. How did you handle it?",
            category: "behavioral",
            hint: "Be honest but diplomatic. Focus on the resolution, not the conflict.",
            language: "en",
        },
        {
            id: "en007",
            question: "What do you think are the most important trends in mechanical engineering right now?",
            category: "technical",
            hint: "Mention specific topics: AI/ML in design, additive manufacturing, digital twins, green manufacturing.",
            language: "en",
        },
        {
            id: "en008",
            question: "Where do you see yourself in 5 years?",
            category: "general",
            hint: "Connect to the program. Show ambition but be realistic.",
            language: "en",
        },
        {
            id: "en009",
            question: "If you had unlimited resources, what research problem in mechanical engineering would you tackle?",
            category: "technical",
            hint: "Show creativity and passion. Connect to your existing experience.",
            language: "en",
        },
        {
            id: "en010",
            question: "Describe your experience with engineering software tools. Which are you most proficient in?",
            category: "technical",
            hint: "Be honest about proficiency levels. Mention specific projects where you used each tool.",
            language: "en",
        },
    ];

    // 内置中文示例题目（API 不可用时使用）
    const FALLBACK_QUESTIONS_CN = [
        {
            id: "cn001",
            question: "请做一个简短的自我介绍，并说明你为什么选择攻读机械工程方向的研究生。",
            category: "general",
            hint: "控制在1-2分钟内。涵盖：基本信息、本科经历、科研兴趣、读研动机。",
            language: "cn",
        },
        {
            id: "cn002",
            question: "请详细介绍一个你参与过的科研项目。你在其中具体负责了什么工作？遇到了哪些困难，如何解决的？",
            category: "technical",
            hint: "用STAR法则：情境→任务→行动→结果。重点突出你个人的贡献。",
            language: "cn",
        },
        {
            id: "cn003",
            question: "你在本科期间学得最好的一门专业课是什么？请简单介绍一下这门课的核心内容。",
            category: "technical",
            hint: "选一门机械核心课（如机械原理、材料力学），展示扎实的理论基础。",
            language: "cn",
        },
        {
            id: "cn004",
            question: "你为什么选择我们学校？有没有了解过我们学院哪些导师的研究方向？",
            category: "general",
            hint: "做足功课！提具体的导师姓名和其最近的研究工作，不要泛泛而谈。",
            language: "cn",
        },
        {
            id: "cn005",
            question: "描述一次你在团队合作中遇到冲突的经历，你是如何处理的？",
            category: "behavioral",
            hint: "诚实但得体。聚焦于解决方案而非冲突本身，展示沟通和协作能力。",
            language: "cn",
        },
        {
            id: "cn006",
            question: "你认为机械工程领域目前最重要的技术趋势是什么？",
            category: "technical",
            hint: "提及具体方向：AI+设计、增材制造、数字孪生、绿色制造、机器人等。",
            language: "cn",
        },
        {
            id: "cn007",
            question: "你未来的研究兴趣是什么？有没有初步的科研规划？",
            category: "general",
            hint: "与目标学校的优势方向结合，展示你的思考和准备。",
            language: "cn",
        },
        {
            id: "cn008",
            question: "除了我们学校，你还申请了哪些学校？如果都录取了你会怎么选择？",
            category: "behavioral",
            hint: "诚实回答申请情况，但强调对这所学校的偏好和理由。",
            language: "cn",
        },
        {
            id: "cn009",
            question: "研究生阶段你希望从导师那里获得什么样的指导？",
            category: "behavioral",
            hint: "展示你对师生关系的思考，既要有自主性又要愿意接受指导。",
            language: "cn",
        },
        {
            id: "cn010",
            question: "如果让你重新做一次本科毕设或科研项目，你会在哪些方面做出不同的选择？",
            category: "technical",
            hint: "展示反思能力和科研思维，说明你从经验中学到了什么。",
            language: "cn",
        },
    ];

    let questions = [];
    let loaded = false;
    let currentLang = "en";

    /**
     * 从 API 加载题目，支持语言参数
     * @param {string} lang - "cn" 或 "en"
     */
    async function loadQuestions(lang = "en") {
        currentLang = lang;
        if (loaded) return questions;

        try {
            // 随机抽取10道题用于练习（题库可能很大）
            const url = `/api/questions?lang=${lang}&sample=10`;
            const resp = await fetch(url);
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const data = await resp.json();

            // 从最新的会话中提取题目
            const sessions = data.sessions || {};
            const sessionNames = Object.keys(sessions);

            if (sessionNames.length > 0) {
                // Prefer explicit created_at metadata; fall back to session name ordering.
                const latest = sessionNames.sort((a, b) => {
                    const sa = sessions[a] || {};
                    const sb = sessions[b] || {};
                    const ta = Date.parse(sa.created_at || "");
                    const tb = Date.parse(sb.created_at || "");
                    if (!Number.isNaN(ta) && !Number.isNaN(tb)) return tb - ta;
                    if (!Number.isNaN(ta)) return -1;
                    if (!Number.isNaN(tb)) return 1;
                    return b.localeCompare(a);
                })[0];
                questions = (sessions[latest] || []);

                // 如果是数组格式（直接就是questions），保持原样
                if (!Array.isArray(questions)) {
                    questions = sessions[latest].questions || [];
                }

                // 过滤语言
                if (lang === "cn") {
                    questions = questions.filter(q => q.language === "cn" || q.language === "zh");
                } else {
                    questions = questions.filter(q => !q.language || q.language === "en" || q.language === "");
                }

                // 转换格式
                questions = questions.map((q) => ({
                    id: q.id,
                    question: q.question,
                    category: q.category || "general",
                    hint: q.hint || q.purpose || "",
                    language: q.language || "en",
                }));
            }
        } catch (e) {
            console.warn("[QuestionLoader] API 不可用，使用示例题目:", e.message);
        }

        // API 没有数据或出错，使用示例
        if (questions.length === 0) {
            if (lang === "cn") {
                questions = [...FALLBACK_QUESTIONS_CN];
            } else {
                questions = [...FALLBACK_QUESTIONS_EN];
            }
        }

        loaded = true;
        return questions;
    }

    /**
     * 重置加载状态（切换语言时使用）
     */
    function reset() {
        questions = [];
        loaded = false;
    }

    /**
     * 获取所有题目
     */
    function getAll() {
        return questions;
    }

    /**
     * 获取指定题目
     */
    function get(index) {
        if (index >= 0 && index < questions.length) {
            return questions[index];
        }
        return null;
    }

    /**
     * 题目总数
     */
    function count() {
        return questions.length;
    }

    return {
        loadQuestions,
        getAll,
        get,
        count,
        reset,
    };
})();
