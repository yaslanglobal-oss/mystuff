// ==UserScript==
// @name         4399 强力去实名弹窗 (底层对抗版)
// @namespace    http://tampermonkey.net/
// @version      0.6
// @description  利用原生 CSS 注入和属性锁死，定点清除 #Anti_mask 和 #Anti_open，永久释放右键
// @author       YaslanGlobal-OSS
// @match        *://*.4399.com/*
// @grant        none
// @run-at       document-start
// @allFrames    true
// ==/UserScript==
  // ==========================================
    //This script is for learning and research purposes only. 
    //Commercial use or other infringing purposes are strictly prohibited.
    //Please delete it within 24 hours of downloading!
    // ==========================================
(function() {
    'use strict';

    // =========================================================
    // 1. 降维打击：通过原生 CSS 注入直接抹杀元素（效仿 AdGuard 机制）
    // =========================================================
    // 这种方法不依赖 JS 的执行。哪怕网页在后面触发了 debugger 挂起了主线程，
    // 浏览器在渲染层也会直接无视这两个元素，且网站脚本无法通过 JS 覆盖此样式。
    const style = document.createElement('style');
    style.textContent = `
        #Anti_mask, #Anti_open {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
            pointer-events: none !important;
            width: 0 !important;
            height: 0 !important;
        }
        body, html {
            overflow: auto !important;
            pointer-events: auto !important;
        }
    `;
    // 抢在 head 出来前插入到 root，确保最早生效
    (document.head || document.documentElement).appendChild(style);


    // =========================================================
    // 2. 强力锁死右键：防御网站脚本后期的覆盖
    // =========================================================
    // 劫持 document 和 window 的 oncontextmenu 属性，使其永远为 null，
    // 并且用 defineProperty 锁死，让 4399 后续的脚本无法对其重新赋值。
    const lockProperty = (obj, prop) => {
        try {
            Object.defineProperty(obj, prop, {
                get: () => null,
                set: () => { /* 拒绝网站脚本的赋值修改 */ },
                configurable: false
            });
        } catch(e) {}
    };

    lockProperty(document, 'oncontextmenu');
    lockProperty(window, 'oncontextmenu');
    lockProperty(document, 'onselectstart');


    // =========================================================
    // 3. 拦截网站的 addEventListener 限制
    // =========================================================
    // 很多网站通过 addEventListener('contextmenu', ...) 来阻止右键。
    // 我们直接重写这个底层方法，只要发现网站试图监听右键或复制，直接拦截丢弃。
    const originalAddEventListener = EventTarget.prototype.addEventListener;
    EventTarget.prototype.addEventListener = function(type, listener, options) {
        const banEvents = ['contextmenu', 'selectstart', 'copy', 'keydown', 'keypress', 'keyup'];
        if (banEvents.includes(type)) {
            // 拒绝绑定这些限制性事件
            return;
        }
        return originalAddEventListener.call(this, type, listener, options);
    };


    // =========================================================
    // 4. 定时补漏：物理移除（防止某些极端脚本用 Canvas 模拟）
    // =========================================================
    const forceKill = () => {
        ['#Anti_mask', '#Anti_open'].forEach(selector => {
            const el = document.querySelector(selector);
            if (el) el.remove();
        });
    };
    
    // 每 50 毫秒疯狂扫描，持续 10 秒
    const timer = setInterval(forceKill, 50);
    setTimeout(() => clearInterval(timer), 10000);

})();
