/**
 * question_loader.js
 * 从后端 API 加载面试题，或使用内置示例题目。
 */

const QuestionLoader = (() => {
    // 内置示例题目（API 不可用时使用）
    const FALLBACK_QUESTIONS = [
        {
            id: "q001",
            question: "Please introduce yourself and explain why you want to pursue a graduate degree in mechanical engineering.",
            category: "general",
            hint: "Keep it under 2 minutes. Cover: who you are, your major, your research interests, and why grad school.",
        },
        {
            id: "q002",
            question: "Tell me about your most significant research project or technical experience. What was YOUR specific contribution?",
            category: "technical",
            hint: "Use the STAR method: Situation, Task, Action, Result. Emphasize what YOU did, not the team.",
        },
        {
            id: "q003",
            question: "Describe a time when you faced a major technical challenge or experimental failure. How did you handle it?",
            category: "behavioral",
            hint: "Show resilience and problem-solving. What did you learn? What would you do differently?",
        },
        {
            id: "q004",
            question: "Why did you choose our program? Which faculty members' research are you interested in?",
            category: "general",
            hint: "Do your homework. Mention specific professors and their recent work.",
        },
        {
            id: "q005",
            question: "Can you explain the concept of Finite Element Analysis to someone without an engineering background?",
            category: "technical",
            hint: "Start with a simple analogy. Focus on the 'why' and 'when', not just the 'what'.",
        },
        {
            id: "q006",
            question: "Tell me about a situation where you had to collaborate with difficult teammates. How did you handle it?",
            category: "behavioral",
            hint: "Be honest but diplomatic. Focus on the resolution, not the conflict.",
        },
        {
            id: "q007",
            question: "What do you think are the most important trends in mechanical engineering right now?",
            category: "technical",
            hint: "Mention specific topics: AI/ML in design, additive manufacturing, digital twins, green manufacturing.",
        },
        {
            id: "q008",
            question: "Where do you see yourself in 5 years?",
            category: "general",
            hint: "Connect to the program. Show ambition but be realistic.",
        },
        {
            id: "q009",
            question: "If you had unlimited resources, what research problem in mechanical engineering would you tackle?",
            category: "technical",
            hint: "Show creativity and passion. Connect to your existing experience.",
        },
        {
            id: "q010",
            question: "Describe your experience with engineering software tools. Which are you most proficient in?",
            category: "technical",
            hint: "Be honest about proficiency levels. Mention specific projects where you used each tool.",
        },
    ];

    let questions = [];
    let loaded = false;

    /**
     * 从 API 加载题目
     */
    async function loadQuestions() {
        if (loaded) return questions;

        try {
            const resp = await fetch("/api/questions");
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const data = await resp.json();

            // 从最新的会话中提取题目
            const sessions = data.sessions || {};
            const sessionNames = Object.keys(sessions);

            if (sessionNames.length > 0) {
                // 取最新的会话
                const latest = sessionNames.sort().reverse()[0];
                questions = sessions[latest].questions || [];

                // 转换格式
                questions = questions.map((q) => ({
                    id: q.id,
                    question: q.question,
                    category: q.category || "general",
                    hint: q.hint || q.purpose || "",
                }));
            }
        } catch (e) {
            console.warn("[QuestionLoader] API 不可用，使用示例题目:", e.message);
        }

        // API 没有数据或出错，使用示例
        if (questions.length === 0) {
            questions = [...FALLBACK_QUESTIONS];
        }

        loaded = true;
        return questions;
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
    };
})();
