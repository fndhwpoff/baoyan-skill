/**
 * camera.js
 * 摄像头和录制管理模块。
 * 使用 MediaDevices API 获取摄像头画面，MediaRecorder API 录制视频。
 * 同时使用 Web Speech API 进行语音转写（Chrome/Edge 支持）。
 * 所有录制数据仅存储在浏览器内存中（Blob），不会上传。
 */

const Camera = (() => {
    let stream = null;
    let recorder = null;
    let recordedChunks = [];
    let currentBlob = null;
    let speechRecognition = null;
    let transcript = "";
    let recognitionLang = "en-US";
    let speechSupported = false;

    // 检查 Web Speech API 支持
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    speechSupported = !!SpeechRecognition;

    /**
     * 请求摄像头和麦克风权限
     */
    async function request(video = true, audio = true) {
        try {
            const constraints = {
                video: video ? { width: 1280, height: 720, facingMode: "user" } : false,
                audio: audio,
            };
            stream = await navigator.mediaDevices.getUserMedia(constraints);
            return stream;
        } catch (err) {
            console.error("[Camera] 权限获取失败:", err);
            if (video) {
                try {
                    console.log("[Camera] 尝试仅音频模式...");
                    stream = await navigator.mediaDevices.getUserMedia({
                        video: false, audio: audio,
                    });
                    return stream;
                } catch (audioErr) {
                    console.error("[Camera] 音频也失败:", audioErr);
                }
            }
            throw err;
        }
    }

    /**
     * 将流附加到 video 元素
     */
    function attachToVideo(videoEl) {
        if (stream && videoEl) {
            videoEl.srcObject = stream;
        }
    }

    /**
     * 设置语音识别语言
     * @param {string} lang - "zh-CN" 或 "en-US"
     */
    function setSpeechLang(lang) {
        recognitionLang = lang || "en-US";
    }

    /**
     * 启动语音识别（与录制同步）
     */
    function startSpeechRecognition() {
        if (!speechSupported) {
            console.warn("[Camera] Web Speech API 不可用（请使用 Chrome 或 Edge）");
            return;
        }

        try {
            speechRecognition = new SpeechRecognition();
            speechRecognition.continuous = true;
            speechRecognition.interimResults = true;
            speechRecognition.lang = recognitionLang;
            transcript = "";

            speechRecognition.onresult = (event) => {
                let interim = "";
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    const result = event.results[i];
                    if (result.isFinal) {
                        transcript += result[0].transcript + " ";
                    } else {
                        interim += result[0].transcript;
                    }
                }
                // 最新转录存储在 transcript 变量中
            };

            speechRecognition.onerror = (event) => {
                console.warn("[Camera] 语音识别错误:", event.error);
                if (event.error === "no-speech") {
                    // 正常，用户可能在思考
                } else if (event.error === "aborted") {
                    // 用户主动停止
                }
            };

            speechRecognition.onend = () => {
                console.log("[Camera] 语音识别结束");
            };

            speechRecognition.start();
            console.log("[Camera] 语音识别已启动, lang:", recognitionLang);
        } catch (err) {
            console.warn("[Camera] 语音识别启动失败:", err);
        }
    }

    /**
     * 停止语音识别
     */
    function stopSpeechRecognition() {
        if (speechRecognition) {
            try {
                speechRecognition.stop();
            } catch (e) {
                // 可能已经停止了
            }
            speechRecognition = null;
        }
    }

    /**
     * 获取转录文本
     */
    function getTranscript() {
        return transcript.trim();
    }

    /**
     * 语音识别是否可用
     */
    function isSpeechSupported() {
        return speechSupported;
    }

    /**
     * 开始录制（同时启动语音识别）
     * @param {string} lang - 语音识别语言 "zh-CN" 或 "en-US"
     */
    function startRecording(lang) {
        return new Promise((resolve, reject) => {
            if (!stream) {
                reject(new Error("没有可用的媒体流"));
                return;
            }

            // 设置语言
            if (lang) setSpeechLang(lang);

            recordedChunks = [];
            currentBlob = null;

            try {
                const mimeType = getSupportedMimeType();
                recorder = new MediaRecorder(stream, {
                    mimeType: mimeType,
                    videoBitsPerSecond: 1500000,
                });

                recorder.ondataavailable = (event) => {
                    if (event.data && event.data.size > 0) {
                        recordedChunks.push(event.data);
                    }
                };

                recorder.onstop = () => {
                    currentBlob = new Blob(recordedChunks, { type: mimeType });
                    recordedChunks = [];
                };

                recorder.onerror = (event) => {
                    console.error("[Camera] 录制错误:", event.error);
                    reject(event.error);
                };

                recorder.start(1000);

                // 同步启动语音识别
                startSpeechRecognition();

                resolve();
            } catch (err) {
                reject(err);
            }
        });
    }

    /**
     * 停止录制（同时停止语音识别）
     */
    function stopRecording() {
        return new Promise((resolve, reject) => {
            // 停止语音识别
            stopSpeechRecognition();

            if (!recorder || recorder.state === "inactive") {
                resolve(currentBlob);
                return;
            }

            recorder.onstop = () => {
                currentBlob = new Blob(recordedChunks, {
                    type: recorder.mimeType || "video/webm",
                });
                recordedChunks = [];
                resolve(currentBlob);
            };

            try {
                recorder.stop();
            } catch (err) {
                reject(err);
            }
        });
    }

    /**
     * 获取当前录制结果
     */
    function getBlob() {
        return currentBlob;
    }

    /**
     * 将 Blob URL 附加到 video 元素播放
     */
    function playBlobOn(videoEl) {
        if (currentBlob && videoEl) {
            const url = URL.createObjectURL(currentBlob);
            videoEl.src = url;
            videoEl.load();
        }
    }

    /**
     * 清理之前的 Blob URL
     */
    function revokeBlobUrl(videoEl) {
        if (videoEl && videoEl.src && videoEl.src.startsWith("blob:")) {
            URL.revokeObjectURL(videoEl.src);
        }
    }

    /**
     * 停止所有轨道，释放摄像头
     */
    function stop() {
        stopSpeechRecognition();
        if (recorder && recorder.state !== "inactive") {
            recorder.stop();
        }
        if (stream) {
            stream.getTracks().forEach((track) => track.stop());
            stream = null;
        }
    }

    /**
     * 检查是否正在录制
     */
    function isRecording() {
        return recorder && recorder.state === "recording";
    }

    /**
     * 获取浏览器支持的 MIME 类型
     */
    function getSupportedMimeType() {
        const types = [
            "video/webm;codecs=vp9,opus",
            "video/webm;codecs=vp8,opus",
            "video/webm;codecs=h264,opus",
            "video/webm",
            "video/mp4",
        ];
        for (const type of types) {
            if (MediaRecorder.isTypeSupported(type)) return type;
        }
        return "video/webm";
    }

    /**
     * 释放所有资源
     */
    function cleanup() {
        stop();
        currentBlob = null;
        recordedChunks = [];
        transcript = "";
    }

    return {
        request,
        attachToVideo,
        startRecording,
        stopRecording,
        getBlob,
        playBlobOn,
        revokeBlobUrl,
        stop,
        isRecording,
        cleanup,
        getTranscript,
        isSpeechSupported,
        setSpeechLang,
    };
})();
