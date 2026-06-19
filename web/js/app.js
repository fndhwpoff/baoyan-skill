/**
 * app.js
 * 面试练习 — 主控制器（支持中英文模式）
 *
 * 状态机：idle → camera-request → ready → practicing → complete
 * practicing 子状态：question-show → preparing → recording → reviewing
 */

const App = (() => {
    // ========== DOM 引用 ==========
    const $ = (sel) => document.querySelector(sel);
    const $$ = (sel) => document.querySelectorAll(sel);

    // ========== i18n ==========
    const I18N = {
        cn: {
            title: "🎓 保研面试练习",
            subtitle: "Chinese Interview Practice",
            idleTitle: "准备好练习保研面试了吗？",
            idleDesc: "模拟真实面试场景，使用摄像头进行问答练习。所有录制内容仅保存在你的浏览器中，不会上传。",
            feature1: "显示面试题",
            feature2: "30秒准备 + 90秒作答",
            feature3: "摄像头录制 + 回放",
            feature4: "隐私安全，不上传",
            startBtn: "开始练习",
            cameraTitle: "需要摄像头和麦克风权限",
            cameraDesc: "用于录制你的面试回答。录制内容仅在本地浏览器中。",
            allowCamera: "允许摄像头",
            noCamera: "不使用摄像头，仅音频（或纯文字模式）",
            readyTitle: "摄像头已就绪",
            loadedQuestions: "已加载",
            loadedQuestionsEnd: "道题目",
            startFirst: "开始第一题",
            startHint: "点击按钮后显示题目，计时开始",
            questionNum: "第",
            questionNumEnd: "题",
            loading: "加载中...",
            preparing: "准备中...",
            skip: "跳过",
            startAnswer: "开始作答",
            stopAnswer: "结束作答",
            nextQuestion: "下一题",
            recording: "录制中",
            recordingDone: "录制完成",
            timeUp: "时间到！",
            timeUpStart: "时间到！开始作答",
            second: "秒",
            completing: "回答中...",
            completeTitle: "练习完成！",
            completeMsg: "你已完成",
            completeMsgEnd: "道题目。",
            totalQuestions: "总题目数",
            answered: "已作答",
            skipped: "已跳过",
            practiceAgain: "再练一次",
            close: "关闭",
            retry: "重试",
            errorTitle: "出错了",
            noQuestions: "没有题目",
            noQuestionsMsg: "请先生成面试题（使用 /保研 resume 功能）。",
            cameraError: "摄像头不可用",
            cameraDenied: "摄像头/麦克风权限被拒绝。请在浏览器设置中允许摄像头权限后重试。",
            cameraNotFound: "未检测到摄像头或麦克风设备。",
            cameraDeviceError: "设备访问错误",
            footer1: "保研skill · 面试练习",
            footer2: "录制内容仅在本地浏览器中，不会上传",
            langToggle: "🌐 English",
            feedbackBtn: "🤖 AI 点评",
            feedbackTitle: "AI 面试反馈",
            feedbackContent: "内容质量",
            feedbackFluency: "语言流利度",
            feedbackLogic: "逻辑结构",
            feedbackOverall: "综合评分",
            feedbackHint: "点击后可获取 AI 对你的回答的点评",
        },
        en: {
            title: "🎓 Grad School Interview Practice",
            subtitle: "English Interview Practice",
            idleTitle: "Ready to practice for your grad school interview?",
            idleDesc: "Simulate real interview scenarios with webcam recording. All recordings stay in your browser only.",
            feature1: "Display interview questions",
            feature2: "30s prep + 90s answer",
            feature3: "Webcam recording + playback",
            feature4: "Privacy-safe, no upload",
            startBtn: "Start Practice",
            cameraTitle: "Camera & Microphone Required",
            cameraDesc: "Used to record your answers. Recordings stay local in your browser.",
            allowCamera: "Allow Camera",
            noCamera: "No camera — audio only (or text mode)",
            readyTitle: "Camera Ready",
            loadedQuestions: "Loaded",
            loadedQuestionsEnd: "questions",
            startFirst: "Begin First Question",
            startHint: "Click to show the question and start timer",
            questionNum: "Q",
            questionNumEnd: "",
            loading: "Loading...",
            preparing: "Preparing...",
            skip: "Skip",
            startAnswer: "Start Answering",
            stopAnswer: "Stop",
            nextQuestion: "Next",
            recording: "Recording",
            recordingDone: "Recording Complete",
            timeUp: "Time's up!",
            timeUpStart: "Time's up! Starting recording",
            second: "s",
            completing: "Recording...",
            completeTitle: "Practice Complete!",
            completeMsg: "You have completed",
            completeMsgEnd: "questions.",
            totalQuestions: "Total Questions",
            answered: "Answered",
            skipped: "Skipped",
            practiceAgain: "Practice Again",
            close: "Close",
            retry: "Retry",
            errorTitle: "Error",
            noQuestions: "No Questions",
            noQuestionsMsg: "Please generate interview questions first (use /保研 resume).",
            cameraError: "Camera Unavailable",
            cameraDenied: "Camera/microphone permission denied. Please allow in browser settings and retry.",
            cameraNotFound: "No camera or microphone detected.",
            cameraDeviceError: "Device access error",
            footer1: "保研skill · Interview Practice",
            footer2: "Recordings stay in your browser, never uploaded",
            langToggle: "🌐 中文模式",
            feedbackBtn: "🤖 Get AI Feedback",
            feedbackTitle: "AI Feedback",
            feedbackContent: "Content Quality",
            feedbackFluency: "Language Fluency",
            feedbackLogic: "Logical Structure",
            feedbackOverall: "Overall Score",
            feedbackHint: "Get AI evaluation of your answer",
        },
    };

    let currentLang = localStorage.getItem("interview-lang") || "en";

    function t(key) {
        return (I18N[currentLang] && I18N[currentLang][key]) || (I18N["en"][key]) || key;
    }

    function setLang(lang) {
        currentLang = lang;
        localStorage.setItem("interview-lang", lang);
        updateAllUIText();
        // 重新加载对应语言的题目
        QuestionLoader.reset();
        QuestionLoader.loadQuestions(lang);
    }

    function updateAllUIText() {
        // 更新所有带 data-i18n 属性的元素
        document.querySelectorAll("[data-i18n]").forEach(el => {
            const key = el.getAttribute("data-i18n");
            const text = t(key);
            if (text) el.textContent = text;
        });
        // 更新占位文本
        document.querySelectorAll("[data-i18n-placeholder]").forEach(el => {
            const key = el.getAttribute("data-i18n-placeholder");
            const text = t(key);
            if (text) el.setAttribute("placeholder", text);
        });
        // 更新语言切换按钮
        const toggleBtn = $("#btn-lang-toggle");
        if (toggleBtn) {
            toggleBtn.textContent = currentLang === "cn" ? t("langToggle") : t("langToggle");
        }
        // 更新页面title
        document.title = t("title");
        // 更新 header
        const h1 = document.querySelector(".app-header h1");
        if (h1) h1.textContent = t("title");
        const subtitle = document.querySelector(".app-header .subtitle");
        if (subtitle) subtitle.textContent = t("subtitle");
        // 更新 footer
        const footerSpans = document.querySelectorAll(".app-footer span");
        if (footerSpans.length >= 2) {
            footerSpans[0].textContent = t("footer1");
            footerSpans[2].textContent = t("footer2");
        }
    }

    // ========== 状态 ==========
    let currentState = "idle";
    let currentQuestionIndex = 0;
    let questions = [];
    let completedQuestions = [];
    let useVideo = true;

    // 计时器
    let timerInterval = null;
    let timerSeconds = 0;
    const PREP_TIME = 30;
    const ANSWER_TIME = 90;

    // ========== 初始化 ==========
    async function init() {
        bindEvents();
        updateAllUIText();
        switchTo("idle");
        // 预加载默认语言题目
        QuestionLoader.loadQuestions(currentLang);
    }

    // ========== 事件绑定 ==========
    function bindEvents() {
        // 首页按钮
        $("#btn-start")?.addEventListener("click", handleStart);

        // 语言切换
        $("#btn-lang-toggle")?.addEventListener("click", () => {
            const newLang = currentLang === "cn" ? "en" : "cn";
            setLang(newLang);
        });

        // 摄像头权限
        $("#btn-request-camera")?.addEventListener("click", handleRequestCamera);
        $("#check-no-camera")?.addEventListener("change", (e) => {
            useVideo = !e.target.checked;
        });

        // 就绪页
        $("#btn-next-question")?.addEventListener("click", handleStartPractice);

        // 答题页
        $("#btn-start-recording")?.addEventListener("click", handleStartRecording);
        $("#btn-stop-recording")?.addEventListener("click", handleStopRecording);
        $("#btn-skip")?.addEventListener("click", handleSkip);
        $("#btn-next-after")?.addEventListener("click", handleNextQuestion);

        // 完成页
        $("#btn-restart")?.addEventListener("click", handleRestart);
        $("#btn-close")?.addEventListener("click", () => window.close());
        $("#btn-retry")?.addEventListener("click", handleStart);
    }

    // ========== 状态切换 ==========
    function switchTo(state, data = {}) {
        $$(".state-panel").forEach((el) => el.classList.remove("active"));

        const panel = $(`#state-${state}`);
        if (panel) {
            panel.classList.add("active");
        }

        currentState = state;
        console.log(`[App] 状态: ${state}`, data);
    }

    // ========== 处理：开始 ==========
    async function handleStart() {
        Camera.cleanup();
        questions = [];
        completedQuestions = [];
        currentQuestionIndex = 0;
        clearTimer();

        // 重新加载当前语言的题目
        QuestionLoader.reset();
        switchTo("camera-request");
    }

    // ========== 处理：请求摄像头 ==========
    async function handleRequestCamera() {
        try {
            const stream = await Camera.request(useVideo, true);
            if (useVideo && stream.getVideoTracks().length > 0) {
                Camera.attachToVideo($("#video-preview"));
                $("#camera-placeholder").classList.add("hidden");
                $("#video-preview").classList.remove("hidden");
            } else {
                $("#video-preview").classList.add("hidden");
                $("#camera-placeholder").classList.remove("hidden");
            }

            // 加载当前语言的题目
            questions = await QuestionLoader.loadQuestions(currentLang);

            // 更新UI
            $("#total-questions").textContent = questions.length;

            if (questions.length === 0) {
                switchTo("error", {
                    title: t("noQuestions"),
                    message: t("noQuestionsMsg"),
                });
                return;
            }

            switchTo("ready");

            // 预加载摄像头到答题页
            Camera.attachToVideo($("#video-practice-preview"));
        } catch (err) {
            console.error("[App] 摄像头失败:", err);
            let message = t("cameraDeviceError") + ": " + err.message;
            if (err.name === "NotAllowedError") {
                message = t("cameraDenied");
            } else if (err.name === "NotFoundError") {
                message = t("cameraNotFound");
            }

            switchTo("error", {
                title: t("cameraError"),
                message: message,
            });
        }
    }

    // ========== 处理：开始答题 ==========
    function handleStartPractice() {
        if (questions.length === 0) return;
        currentQuestionIndex = 0;
        showQuestion(currentQuestionIndex);
        switchTo("practicing");
    }

    // ========== 显示题目 + 开始准备计时 ==========
    function showQuestion(index) {
        if (index >= questions.length) {
            finishPractice();
            return;
        }

        const q = questions[index];
        $("#question-text").textContent = q.question;
        $("#question-hint").textContent = q.hint || "";
        $("#current-question-num").textContent = index + 1;
        $("#total-questions-display").textContent = questions.length;

        // 更新进度条
        const progress = (index / questions.length) * 100;
        $("#progress-fill").style.width = `${progress}%`;

        // 重置按钮状态
        $("#btn-start-recording").classList.remove("hidden");
        $("#btn-skip").classList.remove("hidden");
        $("#btn-stop-recording").classList.add("hidden");
        $("#btn-next-after").classList.add("hidden");
        $("#btn-feedback")?.classList.add("hidden");
        $("#recording-indicator").classList.add("hidden");

        // 隐藏回放
        $("#video-practice-preview").classList.remove("hidden");
        $("#video-practice-playback").classList.add("hidden");

        // 开始准备计时
        startTimer(PREP_TIME, "preparing", () => {
            $("#timer-status").textContent = t("timeUpStart");
            handleStartRecording();
        });

        $("#timer-status").textContent = t("preparing");
        updateTimerDisplay(PREP_TIME);
        updateTimerCircle(PREP_TIME, PREP_TIME);
    }

    // ========== 计时器 ==========
    function startTimer(seconds, phase, onComplete) {
        clearTimer();
        timerSeconds = seconds;
        const total = seconds;

        updateTimerDisplay(seconds);

        timerInterval = setInterval(() => {
            timerSeconds--;
            updateTimerDisplay(timerSeconds);
            updateTimerCircle(timerSeconds, total);

            const circle = $("#timer-progress-circle");
            if (circle) {
                circle.classList.remove("warning", "danger");
                if (timerSeconds <= total * 0.1) {
                    circle.classList.add("danger");
                } else if (timerSeconds <= total * 0.25) {
                    circle.classList.add("warning");
                }
            }

            if (timerSeconds <= 0) {
                clearTimer();
                if (onComplete) onComplete();
            }
        }, 1000);
    }

    function clearTimer() {
        if (timerInterval) {
            clearInterval(timerInterval);
            timerInterval = null;
        }
    }

    function updateTimerDisplay(seconds) {
        $("#timer-count").textContent = seconds;
    }

    function updateTimerCircle(remaining, total) {
        const circle = $("#timer-progress-circle");
        if (circle) {
            const circumference = 283;
            const offset = circumference * (1 - remaining / total);
            circle.style.strokeDashoffset = offset;
        }
    }

    // ========== 处理：开始录制 ==========
    async function handleStartRecording() {
        clearTimer();

        try {
            // 传递语音识别语言
            const speechLang = currentLang === "cn" ? "zh-CN" : "en-US";
            await Camera.startRecording(speechLang);

            // 更新UI
            $("#btn-start-recording").classList.add("hidden");
            $("#btn-stop-recording").classList.remove("hidden");
            $("#btn-skip").classList.add("hidden");
            $("#recording-indicator").classList.remove("hidden");
            // 更新录制指示器文本
            const recSpan = document.querySelector("#recording-indicator span:last-child");
            if (recSpan) recSpan.textContent = t("recording");
            $("#timer-status").textContent = t("completing");

            const circle = $("#timer-progress-circle");
            if (circle) {
                circle.classList.remove("warning", "danger");
            }

            startTimer(ANSWER_TIME, "recording", () => {
                $("#timer-status").textContent = t("timeUp");
                handleStopRecording();
            });

            updateTimerCircle(ANSWER_TIME, ANSWER_TIME);
        } catch (err) {
            console.error("[App] 录制失败:", err);
            alert(`录制启动失败: ${err.message}`);
            showQuestion(currentQuestionIndex);
        }
    }

    // ========== 处理：停止录制 ==========
    async function handleStopRecording() {
        clearTimer();
        try {
            const blob = await Camera.stopRecording();
            $("#btn-stop-recording").classList.add("hidden");
            $("#btn-next-after").classList.remove("hidden");
            $("#recording-indicator").classList.add("hidden");
            $("#timer-status").textContent = t("recordingDone");
            if (blob && blob.size > 0) {
                Camera.revokeBlobUrl($("#video-practice-playback"));
                Camera.playBlobOn($("#video-practice-playback"));
                $("#video-practice-preview").classList.add("hidden");
                $("#video-practice-playback").classList.remove("hidden");
            }
            markCompleted(currentQuestionIndex);
        } catch (err) {
            console.error("[App] 停止录制失败:", err);
        }
    }

    // ========== 处理：跳过 ==========
    function handleSkip() {
        clearTimer();
        Camera.stopRecording();
        handleNextQuestion();
    }

    // ========== 处理：下一题 ==========
    function handleNextQuestion() {
        clearTimer();
        Camera.revokeBlobUrl($("#video-practice-playback"));

        $("#video-practice-preview").classList.remove("hidden");
        $("#video-practice-playback").classList.add("hidden");
        Camera.attachToVideo($("#video-practice-preview"));

        currentQuestionIndex++;
        if (currentQuestionIndex >= questions.length) {
            finishPractice();
        } else {
            showQuestion(currentQuestionIndex);
        }
    }

    // ========== 标记完成 ==========
    function markCompleted(index) {
        if (!completedQuestions.includes(index)) {
            completedQuestions.push(index);
        }
    }

    // ========== 完成练习 ==========
    function finishPractice() {
        clearTimer();
        Camera.stop();

        $("#completed-count").textContent = completedQuestions.length;
        $("#btn-feedback")?.classList.add("hidden");

        const stats = $("#complete-stats");
        stats.innerHTML = `
            <div class="stat-item">
                <span>${t("totalQuestions")}</span>
                <strong>${questions.length}</strong>
            </div>
            <div class="stat-item">
                <span>${t("answered")}</span>
                <strong>${completedQuestions.length}</strong>
            </div>
            <div class="stat-item">
                <span>${t("skipped")}</span>
                <strong>${questions.length - completedQuestions.length}</strong>
            </div>
        `;

        // 更新完成页标题
        const completeTitle = document.querySelector("#state-complete h2");
        if (completeTitle) completeTitle.textContent = t("completeTitle");
        const completeDesc = document.querySelector("#state-complete .hero-desc");
        if (completeDesc) {
            completeDesc.innerHTML = `${t("completeMsg")} <strong id="completed-count">${completedQuestions.length}</strong> ${t("completeMsgEnd")}`;
        }

        switchTo("complete");
    }

    // ========== 重新开始 ==========
    function handleRestart() {
        Camera.cleanup();
        questions = [];
        completedQuestions = [];
        currentQuestionIndex = 0;
        clearTimer();

        Camera.revokeBlobUrl($("#video-practice-playback"));

        switchTo("camera-request");
    }

    // ========== 错误处理 ==========
    const originalSwitchTo = switchTo;
    switchTo = function (state, data = {}) {
        originalSwitchTo(state, data);
        if (state === "error") {
            if (data.title) $("#error-title").textContent = data.title;
            if (data.message) $("#error-message").textContent = data.message;
        }
    };

    // ========== 启动 ==========
    document.addEventListener("DOMContentLoaded", init);

    return {
        switchTo,
        t,
        getLang: () => currentLang,
    };
})();
