/**
 * camera.js
 * 摄像头和录制管理模块。
 * 使用 MediaDevices API 获取摄像头画面，MediaRecorder API 录制视频。
 * 所有录制数据仅存储在浏览器内存中（Blob），不会上传。
 */

const Camera = (() => {
    let stream = null;
    let recorder = null;
    let recordedChunks = [];
    let currentBlob = null;

    /**
     * 请求摄像头和麦克风权限
     * @param {boolean} video - 是否请求视频
     * @param {boolean} audio - 是否请求音频
     * @returns {Promise<MediaStream>}
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

            // 尝试降级：仅音频
            if (video) {
                try {
                    console.log("[Camera] 尝试仅音频模式...");
                    stream = await navigator.mediaDevices.getUserMedia({
                        video: false,
                        audio: audio,
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
     * @param {HTMLVideoElement} videoEl
     */
    function attachToVideo(videoEl) {
        if (stream && videoEl) {
            videoEl.srcObject = stream;
        }
    }

    /**
     * 开始录制
     * @returns {Promise<void>}
     */
    function startRecording() {
        return new Promise((resolve, reject) => {
            if (!stream) {
                reject(new Error("没有可用的媒体流"));
                return;
            }

            recordedChunks = [];
            currentBlob = null;

            try {
                // 检查支持的 MIME 类型
                const mimeType = getSupportedMimeType();
                recorder = new MediaRecorder(stream, {
                    mimeType: mimeType,
                    videoBitsPerSecond: 1500000, // 1.5 Mbps
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

                recorder.start(1000); // 每1秒收集一次数据
                resolve();
            } catch (err) {
                reject(err);
            }
        });
    }

    /**
     * 停止录制
     * @returns {Promise<Blob>} 录制的视频 Blob
     */
    function stopRecording() {
        return new Promise((resolve, reject) => {
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
     * @param {HTMLVideoElement} videoEl
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
     * @param {HTMLVideoElement} videoEl
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
            if (MediaRecorder.isTypeSupported(type)) {
                return type;
            }
        }

        return "video/webm"; // 兜底
    }

    /**
     * 释放所有资源
     */
    function cleanup() {
        stop();
        currentBlob = null;
        recordedChunks = [];
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
    };
})();
