// ==UserScript==
// @name         500px_AI 顶级画质智能下载器 (13.0 相册列表通杀版)
// @namespace    http://tampermonkey.net/
// @version      13.0
// @description  主图与相册列表双向通杀！列表免点开直下2048高清图，智能逆向追溯图片真实名称！
// @author       YaslanGlobal
// @match        https://500px.com/*
// @match        https://*.500px.com/*
// @grant        GM_download
// @run-at       document-start
// ==/UserScript==

    // ==========================================
    //This script is for learning and research purposes only. 
    //Commercial use or other infringing purposes are strictly prohibited.
    //Please delete it within 24 hours of downloading!
    // ==========================================
(function() {
    'use strict';

    // ==========================================
    // 1. 核心破局：环境伪装（穿透沙盒，直拿2048大图）
    // ==========================================
    const targetWindow = (typeof unsafeWindow !== 'undefined') ? unsafeWindow : window;

    Object.defineProperty(targetWindow, 'devicePixelRatio', { get: () => 3 });
    Object.defineProperty(targetWindow.screen, 'width', { get: () => 3840 });
    Object.defineProperty(targetWindow.screen, 'height', { get: () => 2160 });
    Object.defineProperty(targetWindow, 'innerWidth', { get: () => 3840 });
    Object.defineProperty(targetWindow.screen, 'innerHeight', { get: () => 2160 });

    // 恢复原生右键
    targetWindow.addEventListener('contextmenu', function(e) {
        e.stopPropagation();
    }, true);

    // ==========================================
    // 2. 循环监听：转换图片、穿透遮罩、无死角挂载按钮
    // ==========================================
    setInterval(() => {
        // A. 穿透遮罩层
        const shields = document.querySelectorAll('[class*="shield"], [class*="overlay"], .photo-wrapper');
        shields.forEach(el => { el.style.pointerEvents = 'none'; });

        // B. 你的2.0核心逻辑（纯净转换背景图）
        const bgImages = document.querySelectorAll('[style*="background-image"]');
        bgImages.forEach(el => {
            if (!el.dataset.swapped) {
                const bgUrl = el.style.backgroundImage.slice(4, -1).replace(/"/g, "");
                if (bgUrl && bgUrl.startsWith('http')) {
                    let highResUrl = bgUrl;
                    if (highResUrl.includes('m%3D1024')) { highResUrl = highResUrl.replace('m%3D1024', 'm%3D2048'); }
                    else if (highResUrl.includes('size=1024')) { highResUrl = highResUrl.replace('size=1024', 'size=2048'); }

                    const img = document.createElement('img');
                    img.src = highResUrl;
                    img.style.width = '100%'; img.style.height = '100%'; img.style.objectFit = 'contain';
                    img.style.pointerEvents = 'auto';

                    el.style.backgroundImage = 'none';
                    el.appendChild(img);
                    el.dataset.swapped = 'true';
                }
            }
        });

        // C. 【全场景覆盖】：捕捉所有图片容器，智能挂载下载按钮
        const allImgs = document.querySelectorAll('img');
        allImgs.forEach(img => {
            // 过滤：必须是500px的图片，且排除很小的图标和头像（宽度大于120px即认为是相册图或主图）
            if (img.src && img.src.includes('500px') && img.naturalWidth > 120 && !img.src.includes('user')) {
                const container = img.parentElement;

                if (container && !container.dataset.hasBtn) {
                    container.style.position = 'relative';
                    container.style.pointerEvents = 'auto';

                    // 创建悬浮下载按钮（稍微调小了一点，更适合列表紧凑排版）
                    const btn = document.createElement('button');
                    btn.innerText = '💾 2048下载';
                    btn.style.cssText = `
                        position: absolute;
                        top: 8px;
                        left: 8px;
                        z-index: 9999;
                        background: rgba(0, 153, 255, 0.9);
                        color: #fff;
                        border: 1px solid #fff;
                        padding: 4px 8px;
                        border-radius: 4px;
                        cursor: pointer;
                        font-size: 11px;
                        font-weight: bold;
                        box-shadow: 0 2px 6px rgba(0,0,0,0.3);
                        transition: all 0.2s;
                        pointer-events: auto !important;
                    `;

                    btn.onmouseenter = () => { btn.style.background = '#007acc'; };
                    btn.onmouseleave = () => { btn.style.background = 'rgba(0, 153, 255, 0.9)'; };

                    // 绑定智能列表追踪下载
                    btn.onclick = function(e) {
                        e.preventDefault();
                        e.stopPropagation();

                        btn.innerText = '⏳...';

                        // 1. 【核心突围】：强制把缩略图链接重组成 2048 顶级大图链接
                        let downloadUrl = img.src;
                        // 替换所有可能出现的限制分辨率参数
                        downloadUrl = downloadUrl.replace(/m%3D\d+/, 'm%3D2048')
                                                 .replace(/size=\d+/, 'size=2048')
                                                 .replace(/q%3D\d+/, 'q%3D90'); // 确保画质最高

                        // 2. 【智能逆向名字追踪】
                        let title = '';
                        let author = '';

                        // 策略一：如果在详情页，直接抓大标题
                        const mainTitleEl = document.querySelector('h1[class*="title"], [class*="PhotoTitle"], h1');

                        // 判断是否在列表页（通常没有大标题，或者图片有很多个）
                        const isList = document.querySelectorAll('img').length > 5;

                        if (!isList && mainTitleEl && mainTitleEl.innerText) {
                            // 详情页模式
                            title = mainTitleEl.innerText.trim().split('\n')[0];
                            const authorEl = document.querySelector('[class*="author"], [class*="photographer"], [class*="displayName"], [class*="ProfileName"]');
                            if (authorEl) author = authorEl.innerText.trim().split('\n')[0];
                        } else {
                            // 列表页模式：向周围的DOM节点逆向搜寻这张图的名字
                            // 先看图片自带的 alt 属性有没有写名字
                            if (img.alt && img.alt.length > 2 && !img.alt.includes('photo')) {
                                title = img.alt.trim();
                            }

                            // 搜寻父级兄弟节点里有没有文字链接（相册里图片下方通常有作品名链接）
                            if (!title && container.parentElement) {
                                const nearLinks = container.parentElement.querySelectorAll('a, p, div');
                                for (let el of nearLinks) {
                                    if (el.innerText && el.innerText.trim().length > 2 && el.innerText.trim().length < 50 && el !== btn) {
                                        title = el.innerText.trim().split('\n')[0];
                                        break;
                                    }
                                }
                            }
                        }

                        // 兜底策略：如果实在抓不到名字，用相册名加图片特征ID做名字
                        if (!title || title === '500px_Photo') {
                            let albumTitle = document.title.replace(/\s*[\/|-]\s*500px.*/gi, '').trim();
                            // 从URL里捞出图片ID
                            const idMatch = downloadUrl.match(/photo\/(\d+)/);
                            const photoId = idMatch ? idMatch[1] : Math.floor(Math.random() * 10000);
                            title = `${albumTitle}_${photoId}`;
                        }

                        // 格式化文件名
                        const safeTitle = title.replace(/[\\/:*?"<>|]/g, "_");
                        const safeAuthor = author ? ' - ' + author.replace(/[\\/:*?"<>|]/g, "_") : '';
                        const safeFileName = `${safeTitle}${safeAuthor}.jpg`;

                        // 调用油猴特权 API 强制下载 2048 链接
                        GM_download({
                            url: downloadUrl,
                            name: safeFileName,
                            onload: () => {
                                btn.innerText = '✅';
                                setTimeout(() => { btn.innerText = '💾 2048下载'; }, 1500);
                            },
                            onerror: (err) => {
                                console.error('下载失败，尝试原图链接下载:', err);
                                // 备用降级：用捕获到的原链接下
                                GM_download({
                                    url: img.src,
                                    name: safeFileName,
                                    onload: () => { btn.innerText = '✅'; setTimeout(() => { btn.innerText = '💾 2048下载'; }, 1500); },
                                    onerror: () => { btn.innerText = '❌'; setTimeout(() => { btn.innerText = '💾 2048下载'; }, 1500); }
                                });
                            }
                        });
                    };

                    container.appendChild(btn);
                    container.dataset.hasBtn = 'true';
                }
            }
        });
    }, 1000);
})();
