/**
 * app.js
 * 英文面试练习 — 主控制器
 *
 * 状态机：idle → camera-request → ready → practicing → complete
 * practicing 子状态：question-show → preparing → recording → reviewing
 */

const App = (() => {
    // ========== DOM 引用 ==========
    const $ = (sel) => document.querySelector(sel);
    const $$ = (sel) => document.querySelectorAll(sel);

    // ========== 状态 ==========
    let currentState = "idle";
    let currentQuestionIndex = 0;
    let questions = [];
    let completedQuestions = [];
    let useVideo = true;

    // 计时器
    let timerInterval = null;
    let timerSeconds = 0;
    // 准备时间（秒）
    const PREP_TIME = 30;
    // 作答时间（秒）
    const ANSWER_TIME = 90;

    // ========== 初始化 ==========
    async function init() {
        bindEvents();
        switchTo("idle");
    }

    // ========== 事件绑定 ==========
    function bindEvents() {
        // 首页按钮
        $("#btn-start")?.addEventListener("click", handleStart);

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
        // 隐藏所有面板
        $$(".state-panel").forEach((el) => el.classList.remove("active"));

        // 显示目标面板
        const panel = $(`#state-${state}`);
        if (panel) {
            panel.classList.add("active");
        }

        currentState = state;
        console.log(`[App] 状态: ${state}`, data);
    }

    // ========== 处理：开始 ==========
    async function handleStart() {
        // 清理之前的状态
        Camera.cleanup();
        questions = [];
        completedQuestions = [];
        currentQuestionIndex = 0;
        clearTimer();

        // 加载题目
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

            // 加载题目
            questions = await QuestionLoader.loadQuestions();

            // 更新UI
            $("#total-questions").textContent = questions.length;

            if (questions.length === 0) {
                switchTo("error", {
                    title: "没有题目",
                    message: "请先生成英文面试题（使用 /保研 resume 功能）。",
                });
                return;
            }

            switchTo("ready");

            // 预加载摄像头到答题页
            Camera.attachToVideo($("#video-practice-preview"));
        } catch (err) {
            console.error("[App] 摄像头失败:", err);
            let message = "无法访问摄像头和麦克风。";
            if (err.name === "NotAllowedError") {
                message = "摄像头/麦克风权限被拒绝。请在浏览器设置中允许摄像头权限后重试。";
            } else if (err.name === "NotFoundError") {
                message = "未检测到摄像头或麦克风设备。";
            } else {
                message = `设备访问错误: ${err.message}`;
            }

            switchTo("error", {
                title: "摄像头不可用",
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
        $("#recording-indicator").classList.add("hidden");

        // 隐藏回放
        $("#video-practice-preview").classList.remove("hidden");
        $("#video-practice-playback").classList.add("hidden");

        // 开始准备计时
        startTimer(PREP_TIME, "preparing", () => {
            // 准备时间到，自动开始录制
            $("#timer-status").textContent = "时间到！开始作答";
            handleStartRecording();
        });

        $("#timer-status").textContent = "准备中...";
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

            // 颜色变化：剩余25%变黄，10%变红
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
        updateTimerCircle(seconds, timerSeconds > 0 ? timerSeconds : 1);
    }

    function updateTimerCircle(remaining, total) {
        const circle = $("#timer-progress-circle");
        if (circle) {
            const circumference = 283; // 2 * π * 45
            const offset = circumference * (1 - remaining / total);
            circle.style.strokeDashoffset = offset;
        }
    }

    // ========== 处理：开始录制 ==========
    async function handleStartRecording() {
        clearTimer(); // 清除准备计时

        try {
            await Camera.startRecording();

            // 更新UI
            $("#btn-start-recording").classList.add("hidden");
            $("#btn-stop-recording").classList.remove("hidden");
            $("#btn-skip").classList.add("hidden");
            $("#recording-indicator").classList.remove("hidden");
            $("#timer-status").textContent = "作答中...";

            // 重置计时器颜色
            const circle = $("#timer-progress-circle");
            if (circle) {
                circle.classList.remove("warning", "danger");
            }

            // 开始作答计时
            startTimer(ANSWER_TIME, "recording", () => {
                // 时间到，自动停止
                $("#timer-status").textContent = "时间到！";
                handleStopRecording();
            });

            updateTimerCircle(ANSWER_TIME, ANSWER_TIME);
        } catch (err) {
            console.error("[App] 录制失败:", err);
            alert(`录制启动失败: ${err.message}`);
            // 恢复到准备状态
            showQuestion(currentQuestionIndex);
        }
    }

    // ========== 处理：停止录制 ==========
    async function handleStopRecording() {
        clearTimer();

        try {
            const blob = await Camera.stopRecording();

            // 更新UI
            $("#btn-stop-recording").classList.add("hidden");
            $("#btn-next-after").classList.remove("hidden");
            $("#recording-indicator").classList.add("hidden");
            $("#timer-status").textContent = "录制完成";

            // 显示回放
            if (blob && blob.size > 0) {
                Camera.revokeBlobUrl($("#video-practice-playback"));
                Camera.playBlobOn($("#video-practice-playback"));
                $("#video-practice-preview").classList.add("hidden");
                $("#video-practice-playback").classList.remove("hidden");
            }

            // 记录完成
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

        // 恢复预览
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

        // 更新完成页
        $("#completed-count").textContent = completedQuestions.length;

        // 生成统计
        const stats = $("#complete-stats");
        stats.innerHTML = `
            <div class="stat-item">
                <span>总题目数</span>
                <strong>${questions.length}</strong>
            </div>
            <div class="stat-item">
                <span>已作答</span>
                <strong>${completedQuestions.length}</strong>
            </div>
            <div class="stat-item">
                <span>已跳过</span>
                <strong>${questions.length - completedQuestions.length}</strong>
            </div>
        `;

        switchTo("complete");
    }

    // ========== 重新开始 ==========
    function handleRestart() {
        Camera.cleanup();
        questions = [];
        completedQuestions = [];
        currentQuestionIndex = 0;
        clearTimer();

        // 清理回放
        Camera.revokeBlobUrl($("#video-practice-playback"));

        switchTo("camera-request");
    }

    // ========== 错误处理 ==========
    // 当 switchTo("error", data) 被调用时更新错误信息
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
    };
})();
