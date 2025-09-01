(() => {
    "use strict";

    function e(e) {
        return function(e) {
            if (Array.isArray(e)) return t(e)
        }(e) || function(e) {
            if ("undefined" != typeof Symbol && Symbol.iterator in Object(e)) return Array.from(e)
        }(e) || function(e, o) {
            if (e) {
                if ("string" == typeof e) return t(e, o);
                var n = Object.prototype.toString.call(e).slice(8, -1);
                return "Object" === n && e.constructor && (n = e.constructor.name), "Map" === n || "Set" === n ? Array.from(e) : "Arguments" === n || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? t(e, o) : void 0
            }
        }(e) || function() {
            throw new TypeError("Invalid attempt to spread non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.")
        }()
    }

    function t(e, t) {
        (null == t || t > e.length) && (t = e.length);
        for (var o = 0, n = new Array(t); o < t; o++) n[o] = e[o];
        return n
    }
    var o, n, i, a, r, s = (o = ["a[href]", "area[href]", 'input:not([disabled]):not([type="hidden"]):not([aria-hidden])', "select:not([disabled]):not([aria-hidden])", "textarea:not([disabled]):not([aria-hidden])", "button:not([disabled]):not([aria-hidden])", "iframe", "object", "embed", "[contenteditable]", '[tabindex]:not([tabindex^="-"])'], n = function() {
        function t(o) {
            var n = o.targetModal,
                i = o.triggers,
                a = void 0 === i ? [] : i,
                r = o.onShow,
                s = void 0 === r ? function() {} : r,
                c = o.onClose,
                l = void 0 === c ? function() {} : c,
                d = o.openTrigger,
                u = void 0 === d ? "data-micromodal-trigger" : d,
                f = o.closeTrigger,
                h = void 0 === f ? "data-micromodal-close" : f,
                v = o.openClass,
                m = void 0 === v ? "is-open" : v,
                g = o.disableScroll,
                y = void 0 !== g && g,
                b = o.disableFocus,
                p = void 0 !== b && b,
                E = o.awaitCloseAnimation,
                w = void 0 !== E && E,
                k = o.awaitOpenAnimation,
                L = void 0 !== k && k,
                S = o.debugMode,
                A = void 0 !== S && S;
            ! function(e, t) {
                if (!(e instanceof t)) throw new TypeError("Cannot call a class as a function")
            }(this, t), this.modal = "string" == typeof n ? document.getElementById(n) : n, this.config = {
                debugMode: A,
                disableScroll: y,
                openTrigger: u,
                closeTrigger: h,
                openClass: m,
                onShow: s,
                onClose: l,
                awaitCloseAnimation: w,
                awaitOpenAnimation: L,
                disableFocus: p
            }, a.length > 0 && this.registerTriggers.apply(this, e(a)), this.onClick = this.onClick.bind(this), this.onKeydown = this.onKeydown.bind(this)
        }
        var n;
        return (n = [{
            key: "registerTriggers",
            value: function() {
                for (var e = this, t = arguments.length, o = new Array(t), n = 0; n < t; n++) o[n] = arguments[n];
                o.filter(Boolean).forEach(function(t) {
                    t.addEventListener("click", function(t) {
                        return e.showModal(t)
                    })
                })
            }
        }, {
            key: "showModal",
            value: function() {
                var e = this,
                    t = arguments.length > 0 && void 0 !== arguments[0] ? arguments[0] : null;
                this.activeElement = document.activeElement, this.modal.setAttribute("aria-hidden", "false"), this.modal.classList.add(this.config.openClass), this.scrollBehaviour("disable"), this.addEventListeners(), this.config.awaitOpenAnimation ? this.modal.addEventListener("animationend", function t() {
                    e.modal.removeEventListener("animationend", t, !1), e.setFocusToFirstNode()
                }, !1) : this.setFocusToFirstNode(), this.config.onShow(this.modal, this.activeElement, t)
            }
        }, {
            key: "closeModal",
            value: function() {
                var e = arguments.length > 0 && void 0 !== arguments[0] ? arguments[0] : null,
                    t = this.modal;
                if (this.modal.setAttribute("aria-hidden", "true"), this.removeEventListeners(), this.scrollBehaviour("enable"), this.activeElement && this.activeElement.focus && this.activeElement.focus(), this.config.onClose(this.modal, this.activeElement, e), this.config.awaitCloseAnimation) {
                    var o = this.config.openClass;
                    this.modal.addEventListener("animationend", function e() {
                        t.classList.remove(o), t.removeEventListener("animationend", e, !1)
                    }, !1)
                } else t.classList.remove(this.config.openClass)
            }
        }, {
            key: "closeModalByIdOrElement",
            value: function(e) {
                this.modal = "string" == typeof e ? document.getElementById(e) : e, this.modal && this.closeModal()
            }
        }, {
            key: "scrollBehaviour",
            value: function(e) {
                if (this.config.disableScroll) {
                    var t = document.querySelector("body");
                    switch (e) {
                        case "enable":
                            Object.assign(t.style, {
                                overflow: ""
                            });
                            break;
                        case "disable":
                            Object.assign(t.style, {
                                overflow: "hidden"
                            })
                    }
                }
            }
        }, {
            key: "addEventListeners",
            value: function() {
                this.modal.addEventListener("touchstart", this.onClick), this.modal.addEventListener("click", this.onClick), document.addEventListener("keydown", this.onKeydown)
            }
        }, {
            key: "removeEventListeners",
            value: function() {
                this.modal.removeEventListener("touchstart", this.onClick), this.modal.removeEventListener("click", this.onClick), document.removeEventListener("keydown", this.onKeydown)
            }
        }, {
            key: "onClick",
            value: function(e) {
                (e.target.hasAttribute(this.config.closeTrigger) || e.target.parentNode.hasAttribute(this.config.closeTrigger)) && (e.preventDefault(), e.stopPropagation(), this.closeModal(e))
            }
        }, {
            key: "onKeydown",
            value: function(e) {
                27 === e.keyCode && this.closeModal(e), 9 === e.keyCode && this.retainFocus(e)
            }
        }, {
            key: "getFocusableNodes",
            value: function() {
                var t = this.modal.querySelectorAll(o);
                return Array.apply(void 0, e(t))
            }
        }, {
            key: "setFocusToFirstNode",
            value: function() {
                var e = this;
                if (!this.config.disableFocus) {
                    var t = this.getFocusableNodes();
                    if (0 !== t.length) {
                        var o = t.filter(function(t) {
                            return !t.hasAttribute(e.config.closeTrigger)
                        });
                        o.length > 0 && o[0].focus(), 0 === o.length && t[0].focus()
                    }
                }
            }
        }, {
            key: "retainFocus",
            value: function(e) {
                var t = this.getFocusableNodes();
                if (0 !== t.length)
                    if (t = t.filter(function(e) {
                            return null !== e.offsetParent
                        }), this.modal.contains(document.activeElement)) {
                        var o = t.indexOf(document.activeElement);
                        e.shiftKey && 0 === o && (t[t.length - 1].focus(), e.preventDefault()), !e.shiftKey && t.length > 0 && o === t.length - 1 && (t[0].focus(), e.preventDefault())
                    } else t[0].focus()
            }
        }]) && function(e, t) {
            for (var o = 0; o < t.length; o++) {
                var n = t[o];
                n.enumerable = n.enumerable || !1, n.configurable = !0, "value" in n && (n.writable = !0), Object.defineProperty(e, n.key, n)
            }
        }(t.prototype, n), t
    }(), i = null, a = function(e) {
        if ("string" == typeof id ? !document.getElementById(e) : !e) return console.warn("MicroModal: ❗Seems like you have missed %c'".concat(e, "'"), "background-color: #f8f9fa;color: #50596c;font-weight: bold;", "ID somewhere in your code. Refer example below to resolve it."), console.warn("%cExample:", "background-color: #f8f9fa;color: #50596c;font-weight: bold;", '<div class="modal" id="'.concat(e, '"></div>')), !1
    }, r = function(e, t) {
        if (function(e) {
                e.length <= 0 && (console.warn("MicroModal: ❗Please specify at least one %c'micromodal-trigger'", "background-color: #f8f9fa;color: #50596c;font-weight: bold;", "data attribute."), console.warn("%cExample:", "background-color: #f8f9fa;color: #50596c;font-weight: bold;", '<a href="#" data-micromodal-trigger="my-modal"></a>'))
            }(e), !t) return !0;
        for (var o in t) a(o);
        return !0
    }, {
        init: function(t) {
            var o = Object.assign({}, {
                    openTrigger: "data-micromodal-trigger"
                }, t),
                a = e(document.querySelectorAll("[".concat(o.openTrigger, "]"))),
                s = function(e, t) {
                    var o = [];
                    return e.forEach(function(e) {
                        var n = e.attributes[t].value;
                        void 0 === o[n] && (o[n] = []), o[n].push(e)
                    }), o
                }(a, o.openTrigger);
            if (!0 !== o.debugMode || !1 !== r(a, s))
                for (var c in s) {
                    var l = s[c];
                    o.targetModal = c, o.triggers = e(l), i = new n(o)
                }
        },
        show: function(e, t) {
            var o = t || {};
            o.targetModal = e, !0 === o.debugMode && !1 === a(e) || (i && i.removeEventListeners(), (i = new n(o)).showModal())
        },
        close: function(e) {
            e ? i.closeModalByIdOrElement(e) : i.closeModal()
        }
    });
    "undefined" != typeof window && (window.MicroModal = s);
    const c = s;
    document.addEventListener("DOMContentLoaded", () => {
        c.init(),
            function() {
                const e = document.querySelector(".seo__readmore"),
                    t = document.querySelector(".seo__hidden-part");
                e && t && e.addEventListener("click", () => {
                    const o = t.classList.toggle("hidden");
                    e.textContent = o ? "Читать полностью..." : "Скрыть"
                })
            }();
        // const e = document.querySelector(".header__actions"),
        //     t = e.querySelector(".search"),
        //     o = e.querySelector(".search-close"),
        //     n = e.querySelector('input[type="search"]');

        // function i() {
        //     e.classList.remove("search-visible")
        // }
        // t.addEventListener("click", t => {
        //     t.stopPropagation(), e.classList.add("search-visible"), n.focus()
        // }), o.addEventListener("click", e => {
        //     e.stopPropagation(), i()
        // }), document.addEventListener("click", t => {
        //     e.contains(t.target) || i()
        // }), document.querySelectorAll(".expand").forEach(e => {
        //     e.addEventListener("click", () => {
        //         e.classList.toggle("active")
        //     })
        // });
        const a = document.querySelectorAll(".tablink");
        a && a.forEach(e => {
            e.addEventListener("click", t => {
                ! function(e, t) {
                    let o = document.querySelectorAll(".tablink");
                    document.querySelectorAll(".tabcontent").forEach(function(e) {
                        e.classList.remove("active")
                    }), o.forEach(function(e) {
                        e.classList.remove("active")
                    }), document.getElementById(t).classList.add("active"), e.currentTarget.classList.add("active")
                }(t, e.getAttribute("data-target"))
            })
        });
    });
    document.addEventListener('DOMContentLoaded', function() {
        const modalContent = document.querySelector('#city-modal .modal__content');
        
        function checkScroll() {
            if (modalContent.scrollHeight > modalContent.clientHeight) {
                modalContent.classList.add('scrollable');
            } else {
                modalContent.classList.remove('scrollable');
            }
        }
        
        // Vérifier au chargement et au redimensionnement
        checkScroll();
        window.addEventListener('resize', checkScroll);
    });
    
    
    const clientMenuItem = document.querySelector(".header__menu-item.client");
    const clientMenu = clientMenuItem.querySelector(".header-menu-sm");

    clientMenuItem.addEventListener("mouseenter", () => {
        clientMenu.classList.add("opened");
    });

    clientMenuItem.addEventListener("mouseleave", (e) => {
        const relatedTarget = e.relatedTarget;
        if (!clientMenu.contains(relatedTarget)) {
            setTimeout(() => {
                if (!clientMenu.matches(':hover')) {
                    clientMenu.classList.remove("opened");
                }
            }, 100);
        }
    });

    clientMenu.addEventListener("mouseleave", (e) => {
        const relatedTarget = e.relatedTarget;
        if (!clientMenuItem.contains(relatedTarget)) {
            clientMenu.classList.remove("opened");
        }
    });

    document.addEventListener("click", (e) => {
        if (!clientMenuItem.contains(e.target) && !clientMenu.contains(e.target)) {
            clientMenu.classList.remove("opened");
        }
    });

    if (window.innerWidth <= 992) {
        clientMenuItem.addEventListener("click", (e) => {
            e.preventDefault();
            clientMenu.classList.toggle("opened");
        });
    }

})();




(function() {
    "use strict";

    const COOKIE_NAME = 'user_cookie_consent';

    function setCookie(name, value, options = {}) {
        if (options.days) {
            let date = new Date();
            date.setTime(date.getTime() + (options.days * 24 * 60 * 60 * 1000));
            options.expires = date.toUTCString();
        }
        const mainDomain = window.location.hostname.split('.').slice(-2).join('.');
        options.domain = `.${mainDomain}`;
        options.path = '/';
        let updatedCookie = encodeURIComponent(name) + "=" + encodeURIComponent(value);
        for (let optionKey in options) {
            updatedCookie += "; " + optionKey;
            let optionValue = options[optionKey];
            if (optionValue !== true) {
                updatedCookie += "=" + optionValue;
            }
        }
        document.cookie = updatedCookie;
    }

    function getCookie(name) {
        const matches = document.cookie.match(new RegExp(
            "(?:^|; )" + name.replace(/([\.$?*|{}\(\)\[\]\\\/\+^])/g, '\\$1') + "=([^;]*)"
        ));
        return matches ? decodeURIComponent(matches[1]) : null;
    }
    
    function initializeCookieBanner() {
        const banner = document.getElementById('cookies-banner');
        if (!banner) return;

        const acceptButtons = banner.querySelectorAll('.accept-cookies');
        if (acceptButtons.length === 0) return;

        const consentGiven = getCookie(COOKIE_NAME) === 'accepted';

        if (!consentGiven) {
            // console.log("[Cookies] No consent found. Displaying banner.");
            banner.classList.add('show');
        }

        acceptButtons.forEach(button => {
            button.addEventListener("click", function(event) {
                event.preventDefault();
                // console.log("[Cookies] Accept button clicked.");
                
                setCookie(COOKIE_NAME, 'accepted', { days: 365 });
                
                banner.classList.remove('show');
            });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeCookieBanner);
    } else {
        initializeCookieBanner();
    }

})();