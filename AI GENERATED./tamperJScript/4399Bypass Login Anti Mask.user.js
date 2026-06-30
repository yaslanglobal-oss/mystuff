// ==UserScript==
// @name         4399 BypassLogin
// @namespace    http://tampermonkey.net/
// @version      1.0.3
// @description  强制释放Unity画布点击、移除左上角干扰框，并保持广告净化。
// @match        *://*.4399.com/*
// @match        *://*.4399.cn/*
// @run-at       document-start
// @grant        none
// @author      YaslanGlobal
//This script borrows from KEJIYU's code and uses AI to clean up personal tags. 
//Here is the source code address:https://dwz.xo.je/CxJJKM
// ==/UserScript==
  // ==========================================
    //This script is for learning and research purposes only. 
    //Commercial use or other infringing purposes are strictly prohibited.
    //Please delete it within 24 hours of downloading!
    // ==========================================
(function() {
    'use strict';

    // 1. CSS 降维打击（针对视觉元素）
    const style = document.createElement('style');
    style.textContent = `
/* --------------------------------------------------------- */
/* A. 广告、弹窗与干扰元素屏蔽（恢复之前净化的广告去除功能） */
/* --------------------------------------------------------- */
[class*="login"], [class*="Anti"], [class*="mask"],
#loginWrap, #realNameWrap, .login-dialog,
.ant-modal-mask, .ant-modal-content,
[id*="pusher"], [class*="guide"],
div[style*="position: fixed"][style*="z-index"][style*="background-color: rgba(0, 0, 0"],
#loginBg, .cmMask, #Anti_mask, #Anti_open,
.fcmdialog, #Anticlose, #btn_login, #Anti_title, #Anti_content, #Anti_tips_show,
[class*="ad"], [class*="banner"], [class*="float"],
[id*="ad"], [id*="banner"], [id*="float"],
.gg_box, .game_gg, .pop_gg, #gg_div, #countdown360p,
a.tdc, img[src*="4399_16561781227.gif"], img[src*="4399_15462930261.png"],
.s-box, .reco, .reco_r, .link_w, a.skin-l, a.skin-r,
a.skinlk-l, a.skinlk-r, .sides, #__top_ico, #func,
/* 兼容 Unity WebGL 框架加载状态下常见的无选择器广告/Logo */
#loading-logo, #loading-spinner, #loading_box, .load-logo {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
    width: 0 !important;
    height: 0 !important;
}

/* --------------------------------------------------------- */
/* B. 核心修复：针对左上角干扰框与画面不可点击 */
/* --------------------------------------------------------- */
/* 强制让网页所有区域及 Unity 画布能够接收鼠标点击 */
html, body, canvas, #unity-container, #unity-canvas, .game-wrap {
    pointer-events: auto !important;
    touch-action: auto !important;
    cursor: default !important;
}

/* 如果 Unity 画布由于鉴权白屏导致无法交互，强制重置其透明度与可见性 */
canvas[style*="opacity: 0"], #unity-canvas[style*="opacity: 0"], .unity-game-canvas[style*="opacity: 0"] {
    opacity: 1 !important;
    visibility: visible !important;
}

/* 解除页面滚动与点击锁定 */
html, body {
    overflow: auto !important;
    overflow-x: hidden !important;
}

/* 精准锁定 Unity 加载进度条上的 Logo 元素，如果其包含 Logo 图像则强制隐藏 */
.loading-logo-image, img.unity-logo, img#loading-logo {
    display: none !important;
}

/* --------------------------------------------------------- */
/* C. 精简导航 UI (保留 GreasyFork 优秀部分) */
/* --------------------------------------------------------- */
div.top {
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    width: 100% !important;
    margin-bottom: 5px !important;
}
`;
    (document.head || document.documentElement).appendChild(style);

    // =========================================================
    // 2. 核心突破：Proxy 代理 window.FT 对象以通过鉴权白屏
    // =========================================================
    // Unity 游戏脚本由于没有登录状态而卡死，通过伪造 FT 对象函数通过检测
    let realFT = window.FT || {};

    const ftHandler = {
        get: function(target, prop, receiver) {
            // 定义需要伪造的函数，全部返回 true/已验证成年人状态
            const fakeTrueFuncs = ['isLogin', 'checkLogin', 'checkRealName', 'isRealName', 'showRealName', 'showLogin'];
            
            if (fakeTrueFuncs.includes(prop)) {
                return function(...args) {
                    console.log(`[整合脚本拦截] 成功伪造 FT.${prop} -> 允许放行`);
                    if (prop === 'getRealName') return { status: 1, age: 25 };
                    return true;
                };
            }
            return Reflect.get(target, prop, receiver);
        },
        set: function(target, prop, value, receiver) {
            return Reflect.set(target, prop, value, receiver);
        }
    };

    Object.defineProperty(window, 'FT', {
        get: () => new Proxy(realFT, ftHandler),
        set: (v) => { realFT = v; },
        configurable: true
    });

    // 伪造全局常规登录状态变量
    window.my_username = "Guest_Player";
    window.is_login = 1;
    window.is_realname = 1;

    // =========================================================
    // 3. 高频轮询清理：物理移除遮罩、左上角框与确保画布点击
    // =========================================================
    setInterval(() => {
        // A. 精准移除干扰元素（包括你在网上找到的选择器与我新增的 Unity Logo）
        const targets = document.querySelectorAll(
            '[class*="mask"], [class*="overlay"], ' +
            '.cmMask, #Anti_mask, #Anti_open, #layer_login, ' +
            '.fcmdialog, #loginBg, #Anticlose, #btn_login, ' +
            '[class*="ad"], [class*="banner"], [class*="float"], ' +
            '#loading-logo, img#loading-logo, #loading_box, #__top_ico'
        );
        targets.forEach(el => el.remove());

        // B. 定时确保滚动条恢复
        if (document.body) document.body.style.overflow = 'auto';
        if (document.documentElement) document.documentElement.style.overflow = 'auto';

        // C. 强力释放游戏画布点击、重置透明度
        // 游戏画面不能点击，通常是有不可见层覆盖或 CSS pointer-events 被禁用
        const unityCanvas = document.querySelector('canvas#unity-canvas, #unity-container canvas, .unity-game-canvas');
        if (unityCanvas) {
            unityCanvas.style.pointerEvents = 'auto';
            unityCanvas.style.zIndex = '999999'; // 确保在最上层
            unityCanvas.style.opacity = '1';
            unityCanvas.style.visibility = 'visible';
            unityCanvas.style.display = 'block';
        }
    }, 100);

})();
